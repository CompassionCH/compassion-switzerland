##############################################################################
#
#    Copyright (C) 2018-2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields, _


class UtmMixin(models.AbstractModel):
    _inherit = 'utm.mixin'

    def get_utms(self, utm_source=False, utm_medium=False, utm_campaign=False):
        """
        Finds the utm records given their name
        :param utm_source:
        :param utm_medium:
        :param utm_campaign:
        :return: dictionary with utm ids
        """
        utm_source_id = False
        if utm_source:
            utm_source_id = self.env['utm.source'].search([
                ('name', '=', utm_source)
            ], limit=1).id
        utm_medium_id = False
        if utm_medium:
            utm_medium_id = self.env['utm.medium'].search([
                ('name', '=', utm_medium)
            ], limit=1).id or utm_medium_id
        utm_campaign_id = False
        if utm_campaign:
            utm_campaign_id = self.env['utm.campaign'].search([
                ('name', '=', utm_campaign)
            ], limit=1).id
        return {
            'source': utm_source_id,
            'medium': utm_medium_id,
            'campaign': utm_campaign_id
        }


class UtmObjects(models.AbstractModel):
    """ Used to add fields in all utm objects. """
    _name = 'utm.object'
    _order = "create_date desc"

    # These three fields will be redefined (source_id)
    contract_ids = fields.One2many(
        'recurring.contract', 'source_id', 'Sponsorships',
        readonly=True
    )
    correspondence_ids = fields.One2many(
        'correspondence', 'source_id', 'Sponsor letters',
        readonly=True
    )
    invoice_line_ids = fields.One2many(
        'account.invoice.line', 'source_id', 'Donations', readonly=True
    )

    sponsorship_count = fields.Integer(
        compute='_compute_sponsorship_count', readonly=True)
    letters_count = fields.Integer(
        compute='_compute_letters_count', readonly=True)
    donation_amount = fields.Float(
        compute='_compute_total_donation', readonly=True)
    total_donation = fields.Char(
        compute='_compute_total_donation', readonly=True)

    def _compute_sponsorship_count(self):
        for utm in self:
            utm.sponsorship_count = len(utm.contract_ids)

    def _compute_letters_count(self):
        for utm in self:
            utm.letters_count = len(utm.correspondence_ids)

    def _compute_total_donation(self):
        # Put a nice formatting
        for utm in self:
            total_donation = 0
            for invoice in utm.invoice_line_ids:
                total_donation += invoice.price_subtotal
            utm.donation_amount = total_donation
            utm.total_donation = 'CHF {:,.2f}'.format(total_donation).replace(
                '.00', '.-').replace(',', "'")

    def open_sponsorships(self):
        return {
            'name': _('Sponsorships'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'recurring.contract',
            'context': self.env.context,
            'domain': [('id', 'in', self.contract_ids.ids)],
            'target': 'current',
        }

    def open_letters(self):
        return {
            'name': _('Letters'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'correspondence',
            'context': self.env.context,
            'domain': [('id', 'in', self.correspondence_ids.ids)],
            'target': 'current',
        }

    def open_invoices(self):
        return {
            'name': _('Invoices'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice.line',
            'context': self.env.context,
            'domain': [('id', 'in', self.invoice_line_ids.ids)],
            'target': 'current',
        }

    def open_clicks(self):
        return {
            'name': _('Clicks'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'link.tracker',
            'context': self.env.context,
            'domain': [('id', 'in', self.link_ids.ids)],
            'target': 'current',
        }


class UtmSource(models.Model):
    _inherit = ['utm.source', 'utm.object']
    _name = 'utm.source'

    name = fields.Char(translate=False)
    mailing_id = fields.Many2one(
        'mail.mass_mailing', compute='_compute_mailing_id'
    )

    link_ids = fields.One2many(
        'link.tracker', 'source_id', 'Clicks', readonly=True
    )

    click_count = fields.Integer(
        compute='_compute_click_count', store=True, readonly=True)

    def _compute_mailing_id(self):
        for source in self:
            source.mailing_id = self.env['mail.mass_mailing'].search([
                ('source_id', '=', source.id)])

    @api.depends('link_ids', 'link_ids.count')
    def _compute_click_count(self):
        for source in self:
            source.click_count = sum(self.env['link.tracker'].search([
                ('source_id', '=', source.id)]).mapped('count'))


class UtmCampaign(models.Model):
    _inherit = ['utm.campaign', 'utm.object']
    _name = 'utm.campaign'

    name = fields.Char(translate=False)
    contract_ids = fields.One2many(inverse_name='campaign_id')
    correspondence_ids = fields.One2many(inverse_name='campaign_id')
    invoice_line_ids = fields.One2many(inverse_name='campaign_id')

    mailing_campaign_id = fields.Many2one(
        'mail.mass_mailing.campaign', compute='_compute_mass_mailing_id'
    )

    link_ids = fields.One2many(
        'link.tracker', 'campaign_id', 'Clicks', readonly=True
    )

    click_count = fields.Integer(
        compute='_compute_click_count', store=True, readonly=True)

    def _compute_mass_mailing_id(self):
        for campaign in self:
            campaign.mailing_campaign_id = self.env[
                'mail.mass_mailing.campaign'].search([
                    ('campaign_id', '=', campaign.id)])

    @api.depends('link_ids', 'link_ids.count')
    def _compute_click_count(self):
        for campaign in self:
            campaign.click_count = sum(self.env['link.tracker'].search([
                ('campaign_id', '=', campaign.id)]).mapped('count'))


class UtmMedium(models.Model):
    _inherit = ['utm.medium', 'utm.object']
    _name = 'utm.medium'

    name = fields.Char(translate=False)
    contract_ids = fields.One2many(inverse_name='medium_id')
    correspondence_ids = fields.One2many(inverse_name='medium_id')
    invoice_line_ids = fields.One2many(inverse_name='medium_id')

    link_ids = fields.One2many(
        'link.tracker', 'medium_id', 'Clicks', readonly=True
    )

    click_count = fields.Integer(
        compute='_compute_click_count', store=True, readonly=True)

    @api.depends('link_ids', 'link_ids.count')
    def _compute_click_count(self):
        for medium in self:
            medium.click_count = sum(self.env['link.tracker'].search([
                ('medium_id', '=', medium.id)]).mapped('count'))
