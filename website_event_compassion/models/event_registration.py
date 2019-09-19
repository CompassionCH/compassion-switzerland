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
import logging
import base64

from datetime import date

from odoo import api, models, fields, _, SUPERUSER_ID
from odoo.addons.website.models.website import slug
from odoo.exceptions import MissingError
from odoo.tools import config, file_open

from odoo.addons.queue_job.job import job

_logger = logging.getLogger(__name__)

# kanban colors
RED = 2
GREEN = 5

try:
    import magic
except ImportError:
    _logger.error("Please install magic to use website_event_compassion")


def _get_file_type(data):
    ftype = magic.from_buffer(base64.b64decode(data), True)
    if 'pdf' in ftype:
        return '.pdf'
    elif 'tiff' in ftype:
        return '.tiff'
    elif 'jpeg' in ftype:
        return '.jpg'
    elif 'png' in ftype:
        return '.png'
    else:
        return ''


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
        index=True, copy=False,
        domain="['|', ('event_type_ids', '=', False),"
               "      ('event_type_ids', '=', event_type_id)]",
        group_expand='_read_group_stage_ids',
        default=lambda r: r._default_stage()
    )
    stage_date = fields.Date(default=fields.Date.today, copy=False)
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
        string='Completed tasks', copy=False,
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
    uuid = fields.Char(default=lambda self: self._get_uuid(), copy=False)
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

    has_signed_travel_contract = fields.Boolean(compute='_compute_step2_tasks')
    has_signed_child_protection = fields.Boolean(
        compute='_compute_step2_tasks')
    passport_uploaded = fields.Boolean(compute='_compute_step2_tasks')
    emergency_ok = fields.Boolean(compute='_compute_step2_tasks')
    criminal_record_uploaded = fields.Boolean(
        compute='_compute_step2_tasks')
    criminal_record = fields.Binary(compute='_compute_criminal_record',
                                    inverse='_inverse_criminal_record')
    medical_discharge = fields.Binary(attachment=True, copy=False)
    medical_survey_id = fields.Many2one(
        'survey.user_input', 'Medical survey', copy=False)
    feedback_survey_id = fields.Many2one(
        'survey.user_input', 'Feedback survey', copy=False)
    requires_medical_discharge = fields.Boolean(
        compute='_compute_requires_medical_discharge', store=True, copy=False
    )

    # Travel info
    #############
    emergency_name = fields.Char('Emergency contact name')
    emergency_phone = fields.Char('Emergency contact phone number')
    emergency_relation_type = fields.Selection([
        ('husband', 'Husband'),
        ('wife', 'Wife'),
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('brother', 'Brother'),
        ('sister', 'Sister'),
        ('son', 'Son'),
        ('daughter', 'Daughter'),
        ('friend', 'Friend'),
        ('other', 'Other')
    ], string='Emergency contact relation type')
    birth_name = fields.Char()
    passport = fields.Binary(
        compute='_compute_passport', inverse='_inverse_passport')
    passport_number = fields.Char()
    passport_expiration_date = fields.Date()
    flight_ids = fields.One2many('event.flight', 'registration_id', 'Flights')

    # Payment fields
    ################
    down_payment_id = fields.Many2one(
        'account.invoice', 'Down payment', copy=False)
    group_visit_invoice_id = fields.Many2one(
        'account.invoice', 'Trip invoice', copy=False)

    survey_count = fields.Integer(compute='_compute_survey_count')

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
    @api.depends('state', 'event_id.state')
    def _compute_website_published(self):
        for registration in self:
            registration.website_published = registration.state in (
                'open', 'done') and registration.event_id.state == 'confirm'

    @api.multi
    def _compute_partner_display_name(self):
        for registration in self:
            registration.partner_display_name = \
                (registration.partner_firstname or '') + ' ' + \
                registration.partner_lastname

    @api.multi
    def _compute_step2_tasks(self):
        contract_task = self.env.ref(
            'website_event_compassion.task_sign_travel')
        protection_task = self.env.ref(
            'website_event_compassion.task_sign_child_protection')
        passport_task = self.env.ref(
            'website_event_compassion.task_passport')
        criminal_task = self.env.ref(
            'website_event_compassion.task_criminal')
        emergency_task = self.env.ref(
            'website_event_compassion.task_urgency_contact')
        for registration in self:
            registration.has_signed_travel_contract = contract_task in \
                registration.completed_task_ids
            registration.has_signed_child_protection = protection_task in \
                registration.completed_task_ids
            registration.passport_uploaded = passport_task in \
                registration.completed_task_ids
            registration.criminal_record_uploaded = criminal_task in \
                registration.completed_task_ids
            registration.emergency_ok = emergency_task in \
                registration.completed_task_ids

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        # retrieve event type from the context and write the domain
        # - ('id', 'in', stages.ids): add columns that should be present
        type_id = self._context.get('default_event_type_id')
        if type_id:
            search_domain = ['|', ('id', 'in', stages.ids), '|',
                             ('event_type_ids', '=', False),
                             ('event_type_ids', '=', type_id)]
        else:
            search_domain = ['|', ('id', 'in', stages.ids),
                             ('event_type_ids', '=', False)]

        # perform search
        stage_ids = stages._search(search_domain, order=order,
                                   access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    @api.model
    def _default_stage(self):
        type_id = self._context.get('default_event_type_id')
        if type_id:
            stage = self.env['event.registration.stage'].search([
                '|', ('event_type_ids', '=', type_id),
                ('event_type_ids', '=', False)
            ], limit=1)
        else:
            stage = self.env['event.registration.stage'].search([
                ('event_type_ids', '=', False)
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

    def _compute_survey_count(self):
        for registration in self:
            event = registration.event_id
            surveys = event.medical_survey_id + event.feedback_survey_id
            registration.survey_count = self.env['survey.user_input']\
                .search_count([
                    ('partner_id', '=', registration.partner_id.id),
                    ('survey_id', 'in', surveys.ids)
                ])

    @api.depends('medical_survey_id', 'medical_survey_id.state')
    def _compute_requires_medical_discharge(self):
        for registration in self:
            if registration.medical_survey_id.state == 'done':
                treatment = registration.medical_survey_id.user_input_line_ids\
                    .filtered(
                        lambda l: l.question_id == self.env.ref(
                            'website_event_compassion.gpms_question_treatment')
                    )
                registration.requires_medical_discharge =\
                    treatment.value_free_text and not treatment.skipped
            else:
                registration.requires_medical_discharge = False

    def _compute_passport(self):
        for registration in self:
            registration.passport = self.env['ir.attachment'].search([
                ('name', 'like', 'Passport'),
                ('res_id', '=', registration.id),
                ('res_model', '=', self._name)
            ], limit=1).datas

    def _inverse_passport(self):
        attachment_obj = self.env['ir.attachment']
        for registration in self:
            passport = registration.passport
            if passport:
                name = 'Passport ' + registration.name + _get_file_type(
                    passport)
                attachment_obj.create({
                    'datas_fname': name,
                    'res_model': self._name,
                    'res_id': registration.id,
                    'datas': passport,
                    'name': name,
                })
                self.write({
                    'completed_task_ids': [
                        (4, self.env.ref(
                            'website_event_compassion.task_passport').id),
                    ]
                })
            else:
                attachment_obj.search([
                    ('name', 'like', 'Passport'),
                    ('res_id', '=', registration.id),
                    ('res_model', '=', self._name)
                ]).unlink()

    def _compute_criminal_record(self):
        for registration in self:
            registration.criminal_record = self.env['ir.attachment'].search([
                ('name', 'like', 'Criminal record'),
                ('res_id', '=', registration.id),
                ('res_model', '=', self._name)
            ], limit=1).datas

    def _inverse_criminal_record(self):
        attachment_obj = self.env['ir.attachment']
        for registration in self:
            criminal_record = registration.criminal_record
            if criminal_record:
                name = 'Criminal record ' + registration.name + \
                    _get_file_type(criminal_record)
                attachment_obj.create({
                    'datas_fname': name,
                    'res_model': self._name,
                    'res_id': registration.id,
                    'datas': criminal_record,
                    'name': name,
                })
                self.write({
                    'completed_task_ids': [
                        (4, self.env.ref(
                            'website_event_compassion.task_criminal').id),
                    ]
                })
            else:
                attachment_obj.search([
                    ('name', 'like', 'Criminal record'),
                    ('res_id', '=', registration.id),
                    ('res_model', '=', self._name)
                ]).unlink()

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.multi
    def write(self, vals):
        if 'stage_id' in vals:
            vals['stage_date'] = fields.Date.today()
        res = super(Event, self).write(vals)
        module = 'website_event_compassion.'
        # Push registration to next stage if all tasks are complete
        if 'completed_task_ids' in vals:
            for registration in self:
                if not registration.incomplete_task_ids:
                    registration.next_stage()
                if vals.get('stage_id') == self.env.ref(
                        module + 'stage_all_attended'
                ).id and registration.event_type_id.travel_features:
                    registration.prepare_feedback_survey()
        return res

    @api.model
    def create(self, values):
        record = super(Event, self).create(values)

        # check the subtype note by default
        # for all the default follower of a new registration
        self.mapped('message_follower_ids').write(
            {'subtype_ids': [(4, self.env.ref('mail.mt_note').id)]})

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
    def button_send_reminder(self):
        """ Create a communication job with a chosen communication config"""

        ctx = {
            'partner_id': self.partner_id_id,
            'object_ids': self.ids
        }

        return {
            'name': _('Choose a communication'),
            'type': 'ir.actions.act_window',
            'res_model': 'event.registration.communication.wizard',
            'view_id': self.env.ref(
                'website_event_compassion.'
                'event_registration_communication_wizard_form').id,
            'view_mode': 'form',
            'target': 'new',
            'context': ctx
        }

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

    @job
    def cancel_registration(self):
        """Cancel registration"""
        return self.button_reg_cancel()

    @api.multi
    def get_event_registration_survey(self):
        event = self.event_id
        surveys = event.medical_survey_id + event.feedback_survey_id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'survey.user_input',
            'name': _('Surveys'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [
                ('survey_id', 'in', surveys.ids),
                ('partner_id', '=', self.partner_id_id)
            ],
            'context': self.env.context,
        }

    ##########################################################################
    #                       STAGE TRANSITION METHODS                         #
    ##########################################################################
    @api.multi
    def next_stage(self):
        """ Transition to next registration stage """
        for registration in self:
            next_stage = self.env['event.registration.stage'].search([
                ('sequence', '>', registration.stage_id.sequence),
                '|',
                ('event_type_ids', 'in',
                 registration.stage_id.event_type_ids.ids),
                ('event_type_ids', '=', False)
            ], limit=1)
            if next_stage:
                registration.write({
                    'stage_id': next_stage.id,
                    'uuid': self._get_uuid()
                })
            if next_stage == self.env.ref(
                    'website_event_compassion.stage_group_pay'):
                registration.prepare_down_payment()
            elif next_stage == self.env.ref(
                    'website_event_compassion.stage_group_documents'):
                registration.prepare_group_visit_payment()
            elif next_stage == self.env.ref(
                    'website_event_compassion.stage_group_medical'):
                registration.prepare_medical_survey()
        # Send potential communications after stage transition
        self.env['event.mail'].with_delay().run_job()
        return True

    def prepare_down_payment(self):
        # Prepare invoice for down payment
        mode_pay_bvr = self.env['account.payment.mode'].sudo().search([
            ('name', '=', 'BVR')
        ], limit=1)
        self.ensure_one()
        event = self.compassion_event_id
        product = self.event_ticket_id.product_id
        name = u'[{}] Down payment'.format(event.name)
        invoice = self.env['account.invoice'].create({
            'origin': name,
            'partner_id': self.partner_id.id,
            'invoice_line_ids': [(0, 0, {
                'quantity': 1.0,
                'price_unit': self.event_ticket_id.price,
                'account_id': product.property_account_income_id.id,
                'name': name,
                'product_id': product.id,
                'account_analytic_id': event.analytic_id.id,
            })],
            'type': 'out_invoice',
            'reference': self.partner_id.generate_bvr_reference(product),
            'payment_mode_id': mode_pay_bvr.id,
        })
        if self.partner_id.state == 'active':
            invoice.action_invoice_open()
        self.down_payment_id = invoice

    def prepare_group_visit_payment(self):
        # Prepare invoice for group visit payment
        mode_pay_bvr = self.env['account.payment.mode'].sudo().search([
            ('name', '=', 'BVR')
        ], limit=1)
        self.ensure_one()
        event = self.compassion_event_id
        invl_vals = []
        tickets = self.event_id.event_ticket_ids
        if self.include_flight:
            flight_ticket = tickets.filtered(
                lambda t: t.product_id.product_tmpl_id == self.env.ref(
                    'website_event_compassion.product_template_flight'))
            product = flight_ticket.product_id
            invl_vals.append({
                'quantity': 1.0,
                'price_unit': flight_ticket.price,
                'account_id': product.property_account_income_id.id,
                'name': product.name,
                'product_id': product.id,
                'account_analytic_id': event.analytic_id.id,
            })
        if not self.double_room_person:
            single_room_ticket = tickets.filtered(
                lambda t: t.product_id.product_tmpl_id == self.env.ref(
                    'website_event_compassion.product_template_single_room'))
            product = single_room_ticket.product_id
            if product and single_room_ticket.price:
                invl_vals.append({
                    'quantity': 1.0,
                    'price_unit': single_room_ticket.price,
                    'account_id': product.property_account_income_id.id,
                    'name': product.name,
                    'product_id': product.id,
                    'account_analytic_id': event.analytic_id.id,
                })
        standard_price = tickets.filtered(
            lambda t: t.product_id.product_tmpl_id == self.env.ref(
                'website_event_compassion.product_template_trip_price'))
        product = standard_price.product_id
        invl_vals.append({
            'quantity': 1.0,
            'price_unit': standard_price.price,
            'account_id': product.property_account_income_id.id,
            'name': product.name,
            'product_id': product.id,
            'account_analytic_id': event.analytic_id.id,
        })
        name = u'[{}] Trip payment'.format(event.name)
        invoice = self.env['account.invoice'].create({
            'origin': name,
            'partner_id': self.partner_id.id,
            'invoice_line_ids': [(0, 0, invl) for invl in invl_vals],
            'type': 'out_invoice',
            'reference': self.partner_id.generate_bvr_reference(product),
            'payment_mode_id': mode_pay_bvr.id,
        })
        if self.partner_id.state == 'active':
            invoice.action_invoice_open()
        self.group_visit_invoice_id = invoice

    def prepare_medical_survey(self):
        # Attach medical survey for user
        self.ensure_one()
        survey = self.event_id.medical_survey_id
        if not survey:
            return
        local_context = survey.action_send_survey().get('context')
        wizard = self.env['survey.mail.compose.message']\
            .with_context(local_context).create({
                'public': 'no_email',
                'phone_partner_ids': [(6, 0, self.partner_id.ids)],
            })
        wizard.onchange_template_id_wrapper()
        wizard.add_new_answer()
        self.medical_survey_id = self.env['survey.user_input'].search([
            ('partner_id', '=', self.partner_id_id),
            ('survey_id', '=', survey.id)
        ], limit=1)

    def prepare_feedback_survey(self):
        # Attach feedback survey for user
        self.ensure_one()
        survey = self.event_id.feedback_survey_id
        if not survey:
            return
        local_context = survey.action_send_survey().get('context')
        wizard = self.env['survey.mail.compose.message']\
            .with_context(local_context).create({
                'public': 'no_email',
                'phone_partner_ids': [(6, 0, self.partner_id.ids)],
            })
        wizard.onchange_template_id_wrapper()
        wizard.add_new_answer()
        self.feedback_survey_id = self.env['survey.user_input'].search([
            ('partner_id', '=', self.partner_id_id),
            ('survey_id', '=', survey.id)
        ], limit=1)

    def send_medical_discharge(self):
        discharge_config = self.env.ref(
            'website_event_compassion.group_visit_medical_discharge_config')
        for registration in self:
            partner = registration.partner_id
            communication = self.env['partner.communication.job']\
                .with_context(no_print=True, lang=partner.lang).create({
                    'partner_id': partner.id,
                    'object_ids': registration.ids,
                    'config_id': discharge_config.id,
                })
            communication.attachment_ids.create({
                'name': _('medical discharge.docx'),
                'report_name': 'report_compassion.a4_bvr',
                'data': file_open(
                    'website_event_compassion/static/src/'
                    'medical_discharge_' + partner.lang + '.docx'
                ).read().encode('base64'),
                'communication_id': communication.id
            })
            communication.send()
        return self.write({
            'completed_task_ids': [
                (4, self.env.ref(
                    'website_event_compassion.task_medical_survey').id),
            ]
        })

    def skip_medical_discharge(self):
        return self.write({
            'completed_task_ids': [
                (4, self.env.ref(
                    'website_event_compassion.task_medical_survey').id),
                (4, self.env.ref(
                    'website_event_compassion.task_medical_discharge').id),
            ]
        })

    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'user_id' in init_values and init_values['user_id'] is False:
            # When the registration is created.
            return 'website_event_compassion.mt_registration_create'
        return super(Event, self)._track_subtype(init_values)
