# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Sebastien Toth <popod@me.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, api, fields


class Attendee(models.Model):
    _inherit = 'calendar.attendee'

    @api.multi
    def _send_mail_to_attendees(self, template_xmlid, force_send=False):
        # only send email to compassion staff
        compassion_staff = self.filtered(
            lambda x: x.partner_id.user_ids and
            x.partner_id.user_ids[0].share is False)

        return super(Attendee, compassion_staff)._send_mail_to_attendees(
            template_xmlid, True)

    @api.multi
    def send_invitation_to_partner(self):
        return super(Attendee, self)._send_mail_to_attendees(
            'calendar.calendar_template_meeting_invitation', True)


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    campaign_event_id = fields.Many2one('utm.campaign', 'Campaign')

    start_timeline = fields.Date(
        compute='_compute_timeline_start',
        inverse='_inverse_timeline_start'
    )
    stop_timeline = fields.Date(
        compute='_compute_timeline_stop',
        inverse='_inverse_timeline_stop'
    )

    @api.multi
    def _compute_timeline_start(self):
        for event in self:
            event.start_timeline = event.start_datetime or event.start_date

    @api.multi
    def _compute_timeline_stop(self):
        for event in self:
            event.stop_timeline = event.stop_datetime or event.stop_date

    def _inverse_timeline_start(self):
        self.start = self.start_timeline

    def _inverse_timeline_stop(self):
        self.stop = self.stop_timeline

    @api.model
    def create(self, vals):
        if 'start_timeline' in vals:
            vals['start'] = vals['start_timeline']
            vals['stop'] = vals['stop_timeline']
        return super(CalendarEvent, self).create(vals)


class EventCompassion(models.Model):
    _inherit = 'crm.event.compassion'

    def _get_calendar_vals(self):
        dico = super(EventCompassion, self)._get_calendar_vals()
        dico['campaign_event_id'] = self.campaign_id.id
        return dico
