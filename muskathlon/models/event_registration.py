# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields, api, _
from odoo.tools import config
from odoo.exceptions import MissingError
from odoo.addons.website.models.website import slug
from odoo.addons.queue_job.job import job, related_action


class MuskathlonRegistration(models.Model):
    _name = 'event.registration'
    _inherit = ['website.published.mixin', 'website.seo.metadata',
                'event.registration']

    compassion_event_id = fields.Many2one(
        related='event_id.compassion_event_id'
    )
    lead_id = fields.Many2one(
        'crm.lead', 'Lead'
    )
    advocate_details_id = fields.Many2one(
        'advocate.details', related='partner_id.advocate_details_id')
    backup_id = fields.Integer(help='Old muskathlon registration id')

    # The 4 following fields avoid giving read access to the public on the
    # res.partner participating in the muskathlon.
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

    sport_discipline_id = fields.Many2one(
        'sport.discipline', 'Sport discipline', required=True
    )
    sport_level = fields.Selection([
        ('beginner', 'Beginner'),
        ('average', 'Average'),
        ('advanced', 'Advanced')
    ])
    sport_level_description = fields.Text('Describe your sport experience')
    amount_objective = fields.Integer('Raise objective', default=10000,
                                      required=True)
    amount_raised = fields.Integer(readonly=True,
                                   compute='_compute_amount_raised')
    amount_raised_percents = fields.Integer(readonly=True,
                                            compute='_compute_amount_raised')

    muskathlon_participant_id = fields.Char(
        related='partner_id.muskathlon_participant_id')

    muskathlon_event_id = fields.Char(
        related='compassion_event_id.muskathlon_event_id')

    website_published = fields.Boolean(
        compute='_compute_website_published', store=True)
    website_url = fields.Char(
        compute='_compute_website_url'
    )

    reg_id = fields.Char(string='Muskathlon registration ID', size=128)
    host = fields.Char(compute='_compute_host', readonly=True)

    _sql_constraints = [
        ('reg_unique', 'unique(event_id,partner_id)',
         'Only one registration per participant/event is allowed!')
    ]

    @api.multi
    def _compute_website_url(self):
        for registration in self:
            registration.website_url = "/event/{}/{}".format(
                slug(registration.compassion_event_id), slug(registration)
            )

    def _compute_amount_raised(self):
        muskathlon_report = self.env['muskathlon.report']

        for registration in self:
            amount_raised = int(sum(
                item.amount for item in muskathlon_report.search([
                    ('user_id', '=', registration.partner_id.id),
                    ('event_id', '=', registration.compassion_event_id.id),
                    ('registration_id', '=', registration.reg_id),
                ])
            ))

            registration.amount_raised = amount_raised
            registration.amount_raised_percents = int(
                amount_raised * 100 / (registration.amount_objective or 10000))

    def _compute_host(self):
        host = config.get('wordpress_host')
        if not host:
            raise MissingError(_('Missing wordpress_host in odoo config file'))
        for registration in self:
            registration.host = host

    @api.multi
    @api.depends(
        'partner_id', 'partner_id.image', 'advocate_details_id',
        'advocate_details_id.quote')
    def _compute_website_published(self):
        required_fields = [
            'partner_preferred_name', 'ambassador_quote',
            'ambassador_picture_1',
        ]
        for registration in self:
            published = True
            for field in required_fields:
                if not getattr(registration, field):
                    published = False
                    break
            registration.website_published = published

    @api.multi
    def _compute_partner_display_name(self):
        for registration in self:
            registration.partner_display_name =\
                registration.partner_firstname + ' ' +\
                registration.partner_lastname

    @api.onchange('event_id')
    def onchange_event_id(self):
        return {
            'domain': {'sport_discipline_id': [
                ('id', 'in',
                 self.compassion_event_id.sport_discipline_ids.ids)]}
        }

    @api.onchange('sport_discipline_id')
    def onchange_sport_discipline(self):
        if self.sport_discipline_id and self.sport_discipline_id not in \
                self.compassion_event_id.sport_discipline_ids:
            self.sport_discipline_id = False
            return {
                'warning': {
                    'title': _('Invalid sport'),
                    'message': _('This sport is not in muskathlon')
                }
            }

    @job(default_channel='root.muskathlon')
    @related_action('related_action_registration')
    def create_muskathlon_lead(self):
        """Create Muskathlon lead for registration"""
        self.ensure_one()
        partner = self.partner_id
        staff_id = self.env['staff.notification.settings'].get_param(
            'muskathlon_lead_notify_id')
        self.lead_id = self.env['crm.lead'].create({
            'name': u'Muskathlon Registration - ' + partner.name,
            'partner_id': partner.id,
            'email_from': partner.email,
            'phone': partner.phone,
            'partner_name': partner.name,
            'street': partner.street,
            'zip': partner.zip,
            'city': partner.city,
            'user_id': staff_id,
            'description': self.sport_level_description,
            'event_id': self.compassion_event_id.id,
            'sales_team_id': self.env.ref(
                'sales_team.salesteam_website_sales').id
        })

    @job(default_channel='root.muskathlon')
    def delete_muskathlon_registration(self):
        """Cancel Muskathlon registration"""
        return self.unlink()
