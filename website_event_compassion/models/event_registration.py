# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields, _
from odoo.addons.website.models.website import slug
from odoo.exceptions import MissingError
from odoo.tools import config

from odoo.addons.queue_job.job import job


class Event(models.Model):
    _inherit = ['website.published.mixin', 'website.seo.metadata',
                'event.registration']
    _name = 'event.registration'
    _description = 'Event registration'
    _order = 'create_date desc'

    user_id = fields.Many2one(
        'res.users', 'Responsible', domain=[('share', '=', False)],
        track_visibility='onchange'
    )
    compassion_event_id = fields.Many2one(
        'crm.event.compassion', related='event_id.compassion_event_id',
        readonly=True
    )
    advocate_details_id = fields.Many2one(
        'advocate.details', related='partner_id.advocate_details_id',
        readonly=True
    )
    fundraising = fields.Boolean(related='event_id.fundraising')
    amount_objective = fields.Integer('Raise objective')
    amount_raised = fields.Float(readonly=True,
                                 compute='_compute_amount_raised')
    amount_raised_percents = fields.Integer(
        readonly=True, compute='_compute_amount_raised_percent'
    )
    website_published = fields.Boolean(
        compute='_compute_website_published', store=True)
    website_url = fields.Char(
        compute='_compute_website_url'
    )
    host_url = fields.Char(compute='_compute_host_url')
    wordpress_host = fields.Char(compute='_compute_wordpress_host')

    # The following fields avoid giving read access to the public on the
    # res.partner participating in the event
    partner_id_id = fields.Integer(related="partner_id.id", readonly=True)
    partner_display_name = fields.Char(compute="_compute_partner_display_name")
    partner_preferred_name = fields.Char(related="partner_id.preferred_name",
                                         readonly=True)
    partner_name = fields.Char(related="partner_id.name", readonly=True)
    ambassador_picture_1 = fields.Binary(related='partner_id.image')
    ambassador_picture_2 = fields.Binary(
        related='partner_id.advocate_details_id.picture_large')
    ambassador_description = fields.Text(
        related='partner_id.advocate_details_id.description')
    ambassador_quote = fields.Text(
        related='partner_id.advocate_details_id.quote')
    partner_firstname = fields.Char(
        related='partner_id.firstname', readonly=True
    )
    partner_lastname = fields.Char(
        related='partner_id.lastname', readonly=True
    )
    partner_gender = fields.Selection(related='partner_id.title.gender',
                                      readonly=True)

    @api.multi
    def _compute_website_url(self):
        for registration in self:
            registration.website_url = "/event/{}/{}".format(
                slug(registration.compassion_event_id), slug(registration)
            )

    def _compute_amount_raised_percent(self):
        for registration in self:
            objective = registration.amount_objective or \
                registration.event_id.participants_amount_objective
            if objective:
                registration.amount_raised_percents = int(
                    registration.amount_raised * 100 / objective)

    def _compute_amount_raised(self):
        for registration in self:
            partner = registration.partner_id
            compassion_event = registration.compassion_event_id
            invoice_lines = self.env['account.invoice.line'].sudo().search([
                ('user_id', '=', partner.id),
                ('state', 'in', ('draft', 'open', 'paid')),
                ('event_id', '=', compassion_event.id)
            ])
            amount_raised = sum(invoice_lines.mapped('price_subtotal'))
            s_value = registration.event_id.sponsorship_donation_value
            if s_value:
                nb_sponsorships = self.env['recurring.contract'].sudo()\
                    .search_count([
                        ('user_id', '=', partner.id),
                        ('origin_id.event_id', '=', compassion_event.id)
                    ])
                amount_raised += nb_sponsorships * s_value
            registration.amount_raised = amount_raised

    def _compute_host_url(self):
        params_obj = self.env['ir.config_parameter']
        host = params_obj.get_param('web.external.url') or \
            params_obj.get_param('web.base.url')
        for registration in self:
            registration.host_url = host

    def _compute_wordpress_host(self):
        host = config.get('wordpress_host')
        if not host:
            raise MissingError(_('Missing wordpress_host in odoo config file'))
        for registration in self:
            registration.wordpress_host = host

    @api.multi
    @api.depends('state')
    def _compute_website_published(self):
        for registration in self:
            registration.website_published = registration.state in (
                'open', 'done')

    @api.multi
    def _compute_partner_display_name(self):
        for registration in self:
            registration.partner_display_name = \
                registration.partner_firstname + ' ' + \
                registration.partner_lastname

    @job
    def cancel_registration(self):
        """Cancel registration"""
        return self.button_reg_cancel()
