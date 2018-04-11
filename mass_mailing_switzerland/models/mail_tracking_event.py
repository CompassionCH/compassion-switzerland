# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, api

import re


class MailTrackingEvent(models.Model):
    _inherit = "mail.tracking.event"

    @api.model
    def create(self, data):
        result = super(MailTrackingEvent, self).create(data)

        if result.url:
            p = re.compile(r'\/([a-zA-Z0-9]{3,6})')
            code = p.findall(result.url)[-1]

            link = self.env['link.tracker.code'].search([('code', '=', code)])

            result.url = link.link_id.url

        return result

    @api.model
    def process_click(self, tracking_email, metadata):
        """ Update mass mailing stats. """
        mass_mail = tracking_email.mass_mailing_id
        if mass_mail:
            # Avoid too much computation
            job = self.env['queue.job'].search_count([
                ('channel', '=', 'root.mass_mailing_switzerland'),
                ('state', 'not in', ['done', 'failed'])
            ])
            if not job:
                mass_mail.with_delay().compute_clicks_ratio()
        return super(MailTrackingEvent, self).process_click(
            tracking_email, metadata)

    @api.model
    def process_unsub(self, tracking_email, metadata):
        """ Update mass mailing stats. """
        mass_mail = tracking_email.mass_mailing_id
        if mass_mail:
            # Avoid too much computation
            job = self.env['queue.job'].search_count([
                ('channel', '=', 'root.mass_mailing_switzerland'),
                ('state', 'not in', ['done', 'failed'])
            ])
            if not job:
                mass_mail.with_delay().compute_unsub_ratio()
        return super(MailTrackingEvent, self).process_unsub(
            tracking_email, metadata)
