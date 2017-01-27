# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import models, api


class MailTrackingEvent(models.Model):
    _inherit = "mail.tracking.event"

    @api.model
    def process_open(self, tracking_email, metadata):
        """ Mark correspondence as read. """
        correspondence = self.env['correspondence'].search([
            ('email_id', '=', tracking_email.mail_id.id),
            ('email_read', '=', False)
        ])
        correspondence.write({
            'email_read': True,
            'letter_read': True
        })
        return super(MailTrackingEvent, self).process_open(
            tracking_email, metadata)
