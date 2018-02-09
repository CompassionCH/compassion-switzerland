# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
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

    # These three fields will be redefined (source_id)
    contract_ids = fields.One2many(
        'recurring.contract', 'source_id', 'Sponsorships',
        readonly=True
    )
    correspondence_ids = fields.One2many(
        'correspondence', 'source_id', 'Sponsor letters',
        readonly=True
    )
    invoice_ids = fields.One2many(
        'account.invoice', 'source_id', 'Donations', readonly=True
    )

    sponsorship_count = fields.Integer(
        compute='_compute_sponsorship_count', store=True, readonly=True)
    letters_count = fields.Integer(
        compute='_compute_letters_count', store=True, readonly=True)
    total_donation = fields.Char(
        compute='_compute_total_donation', store=True, readonly=True)

    @api.depends('contract_ids')
    def _compute_sponsorship_count(self):
        for utm in self:
            utm.sponsorship_count = len(utm.contract_ids)

    @api.depends('correspondence_ids')
    def _compute_letters_count(self):
        for utm in self:
            utm.letters_count = len(utm.correspondence_ids)

    @api.depends('invoice_ids', 'invoice_ids.amount_total')
    def _compute_total_donation(self):
        # Put a nice formatting
        for utm in self:
            total_donation = sum(utm.invoice_ids.mapped('amount_total'))
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
            'res_model': 'account.invoice',
            'context': self.env.context,
            'domain': [('id', 'in', self.invoice_ids.ids)],
            'target': 'current',
        }


class UtmSource(models.Model):
    _inherit = ['utm.source', 'utm.object']
    _name = 'utm.source'

    mailing_id = fields.Many2one(
        'mail.mass_mailing', compute='_compute_mailing_id'
    )

    def _compute_mailing_id(self):
        for source in self:
            source.mailing_id = self.env['mail.mass_mailing'].search([
                ('source_id', '=', source.id)])


class UtmCampaign(models.Model):
    _inherit = ['utm.campaign', 'utm.object']
    _name = 'utm.campaign'

    contract_ids = fields.One2many(inverse_name='campaign_id')
    correspondence_ids = fields.One2many(inverse_name='campaign_id')
    invoice_ids = fields.One2many(inverse_name='campaign_id')

    mailing_campaign_id = fields.Many2one(
        'mail.mass_mailing.campaign', compute='_compute_mass_mailing_id'
    )

    def _compute_mass_mailing_id(self):
        for campaign in self:
            campaign.mailing_campaign_id = self.env[
                'mail.mass_mailing.campaign'].search([
                    ('campaign_id', '=', campaign.id)])


class UtmMedium(models.Model):
    _inherit = ['utm.medium', 'utm.object']
    _name = 'utm.medium'

    contract_ids = fields.One2many(inverse_name='medium_id')
    correspondence_ids = fields.One2many(inverse_name='medium_id')
    invoice_ids = fields.One2many(inverse_name='medium_id')
