# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields
from odoo.addons.event.models.event_mail import _INTERVALS
from odoo.addons.queue_job.job import job


class EventMail(models.Model):
    _inherit = 'event.mail'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    communication_id = fields.Many2one(
        'partner.communication.config', 'Communication',
        domain=[('model_id.model', '=', 'event.registration')],
    )
    template_id = fields.Many2one(related='communication_id.email_template_id')
    interval_type = fields.Selection(selection_add=[
        ('after_stage', 'After stage')
    ])
    stage_id = fields.Many2one('event.registration.stage', 'Stage')

    event_type_id = fields.Many2one('event.type')
    event_id = fields.Many2one(required=False)

    @api.multi
    @api.depends('event_id.state', 'event_id.date_begin', 'interval_type',
                 'interval_unit', 'interval_nbr')
    def _compute_scheduled_date(self):
        """ Add computation for after_stage interval type """
        for scheduler in self:
            if scheduler.interval_type == 'after_stage':
                scheduler.scheduled_date = scheduler.event_id.create_date
            else:
                super(EventMail, scheduler)._compute_scheduled_date()

    @api.multi
    def execute(self):
        """
        Replace execute method to use after_stage interval_type and
        partner communication jobs instead of mail_templates
        :return: True
        """
        for scheduler in self:
            event = scheduler.event_id
            if scheduler.interval_type in ('after_sub', 'after_stage'):
                # update registration lines
                missing_registrations = event.registration_ids.filtered(
                    lambda r: not scheduler.stage_id or
                    r.stage_id == scheduler.stage_id
                ) - scheduler.mail_registration_ids.mapped('registration_id')
                if missing_registrations:
                    scheduler.write({
                        'mail_registration_ids': [
                            (0, 0, {'registration_id': reg.id})
                            for reg in missing_registrations]
                    })
                # execute scheduler on registrations
                scheduler.mail_registration_ids.filtered(
                    lambda reg: reg.scheduled_date and reg.scheduled_date <=
                    fields.Datetime.now()
                ).execute()
            else:
                if not scheduler.mail_sent:
                    for registration in event.registration_ids.filtered(
                            lambda r: r.state != 'cancel'):
                        self.env['partner.communication.job'].create({
                            'partner_id': registration.partner_id.id,
                            'object_ids': registration.ids,
                            'config_id': scheduler.communication_id.id
                        })
                    scheduler.write({'mail_sent': True})
        return True

    @job
    @api.model
    def run_job(self):
        # Run the event mail scheduler cron in asynchronous job
        return self.run()


class EventMailRegistration(models.Model):
    _inherit = 'event.mail.registration'

    @api.depends('registration_id', 'registration_id.stage_date',
                 'scheduler_id.interval_unit', 'scheduler_id.interval_type')
    @api.multi
    def _compute_scheduled_date(self):
        """
        Add computation of scheduled date if interval type is after stage
        :return:
        """
        for mail in self:
            if mail.scheduler_id.interval_type == 'after_stage':
                registration = mail.registration_id
                scheduler = mail.scheduler_id
                if registration.stage_id == scheduler.stage_id:
                    date_open = fields.Datetime.from_string(
                        registration.stage_date)
                    mail.scheduled_date = fields.Datetime.to_string(
                        date_open + _INTERVALS[scheduler.interval_unit](
                            scheduler.interval_nbr))
                else:
                    scheduler.scheduled_date = False
            else:
                super(EventMailRegistration, mail)._compute_scheduled_date()

    @api.multi
    def execute(self):
        """ Replace execute method to send communication instead of using
        email template. """
        for email in self:
            registration = email.registration_id
            if registration.state in ['open', 'done'] and not \
                    email.mail_sent:
                self.env['partner.communication.job'].create({
                    'partner_id': registration.partner_id.id,
                    'object_ids': registration.ids,
                    'config_id': email.scheduler_id.communication_id.id
                })
                email.write({'mail_sent': True})
