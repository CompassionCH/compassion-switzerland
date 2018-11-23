# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import uuid

from datetime import date

from odoo import api, models, fields, _, SUPERUSER_ID
from odoo.addons.website.models.website import slug
from odoo.exceptions import MissingError
from odoo.tools import config

from odoo.addons.queue_job.job import job

# kanban colors
RED = 2
GREEN = 5


class Event(models.Model):
    _inherit = ['website.published.mixin', 'website.seo.metadata',
                'event.registration']
    _name = 'event.registration'
    _description = 'Event registration'
    _order = 'create_date desc'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    user_id = fields.Many2one(
        'res.users', 'Responsible', domain=[('share', '=', False)],
        track_visibility='onchange'
    )
    stage_id = fields.Many2one(
        'event.registration.stage', 'Stage', track_visibility='onchange',
        index=True,
        domain="['|', ('event_type_id', '=', False),"
               "      ('event_type_id', '=', event_type_id)]",
        group_expand='_read_group_stage_ids',
        default=lambda r: r._default_stage()
    )
    stage_date = fields.Date(default=fields.Date.today)
    stage_task_ids = fields.Many2many(
        'event.registration.task', 'event_registration_stage_tasks',
        compute='_compute_stage_tasks'
    )
    incomplete_task_ids = fields.Many2many(
        'event.registration.task', 'event_registration_incomplete_tasks',
        string='Incomplete tasks', compute='_compute_stage_tasks'
    )
    complete_stage_task_ids = fields.Many2many(
        'event.registration.task', 'event_registration_stage_complete_tasks',
        string='Completed tasks', compute='_compute_stage_tasks',
        help='This shows all tasks that the participant completed for the '
             'current stage of his registration.')
    completed_task_ids = fields.Many2many(
        'event.registration.task', 'event_registration_completed_tasks',
        string='Completed tasks',
        help='This shows all tasks that the participant completed for his '
             'registration.')
    color = fields.Integer(compute='_compute_kanban_color')
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
    event_name = fields.Char(related='event_id.name')
    uuid = fields.Char(default=lambda self: self._get_uuid())
    include_flight = fields.Boolean()
    double_room_person = fields.Char('Double room with')

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
    comments = fields.Text()

    medical_check = fields.Boolean()
    medical_validation = fields.Boolean()

    visa_needed = fields.Boolean()
    day_for_a_visa = fields.Integer()

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    def _get_uuid(self):
        return str(uuid.uuid4())

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

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        # retrieve event type from the context and write the domain
        # - ('id', 'in', stages.ids): add columns that should be present
        type_id = self._context.get('default_event_type_id')
        if type_id:
            search_domain = ['|', ('id', 'in', stages.ids), '|',
                             ('event_type_id', '=', False),
                             ('event_type_id', '=', type_id)]
        else:
            search_domain = ['|', ('id', 'in', stages.ids),
                             ('event_type_id', '=', False)]

        # perform search
        stage_ids = stages._search(search_domain, order=order,
                                   access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    @api.model
    def _default_stage(self):
        type_id = self._context.get('default_event_type_id')
        if type_id:
            stage = self.env['event.registration.stage'].search([
                '|', ('event_type_id', '=', type_id),
                ('event_type_id', '=', False)
            ], limit=1)
        else:
            stage = self.env['event.registration.stage'].search([
                ('event_type_id', '=', False)
            ], limit=1)
        return stage.id

    @api.multi
    def _compute_kanban_color(self):
        today = date.today()
        for registration in self:
            stage_date = fields.Date.from_string(
                registration.stage_date) or today
            stage_duration = (today - stage_date).days
            max_duration = registration.stage_id.duration
            if max_duration and stage_duration > max_duration:
                registration.color = RED
            else:
                registration.color = GREEN

    @api.multi
    def _compute_stage_tasks(self):
        for registration in self:
            registration.stage_task_ids = self.env['event.registration.task']\
                .search([('stage_id', '=', registration.stage_id.id)])
            registration.incomplete_task_ids = \
                registration.stage_task_ids - registration.completed_task_ids
            registration.complete_stage_task_ids = \
                registration.completed_task_ids.filtered(
                    lambda t: t.stage_id == registration.stage_id)

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.multi
    def write(self, vals):
        if 'stage_id' in vals:
            vals['stage_date'] = fields.Date.today()
        res = super(Event, self).write(vals)
        # Push registration to next stage if all tasks are complete
        if 'completed_task_ids' in vals:
            for registration in self:
                if not registration.incomplete_task_ids:
                    registration.next_stage()
        return res

    @api.model
    def create(self, values):
        record = super(Event, self).create(values)
        # Set default fundraising objective if none was set
        event = record.event_id
        if not record.amount_objective and event.participants_amount_objective:
            record.amount_objective = event.participants_amount_objective
        return record

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def do_draft(self):
        super(Event, self).do_draft()
        return self.write({
            'stage_id': self.env.ref(
                'website_event_compassion.stage_all_unconfirmed').id
        })

    @api.multi
    def button_reg_close(self):
        super(Event, self).button_reg_close()
        return self.write({
            'stage_id': self.env.ref(
                'website_event_compassion.stage_all_attended').id
        })

    @api.multi
    def button_reg_cancel(self):
        super(Event, self).button_reg_cancel()
        return self.write({
            'stage_id': self.env.ref(
                'website_event_compassion.stage_all_cancelled').id
        })

    @api.multi
    def next_stage(self):
        """ Transition to next registration stage """
        for registration in self:
            next_stage = self.env['event.registration.stage'].search([
                ('sequence', '>', registration.stage_id.sequence),
                '|',
                ('event_type_id', '=', registration.stage_id.event_type_id.id),
                ('event_type_id', '=', False)
            ], limit=1)
            if next_stage:
                registration.write({
                    'stage_id': next_stage.id,
                    'uuid': self._get_uuid()
                })
        return True

    @job
    def cancel_registration(self):
        """Cancel registration"""
        return self.button_reg_cancel()
