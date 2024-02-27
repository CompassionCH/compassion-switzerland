##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class Correspondence(models.Model):
    _inherit = "correspondence"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    email_read = fields.Datetime(
        compute="_compute_email_read", inverse="_inverse_email_read", store=True
    )

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.depends("communication_id.email_id.mail_tracking_ids.tracking_event_ids")
    def _compute_email_read(self):
        for mail in self:
            dates = [
                x.time
                for x in mail.communication_id.email_id.tracking_event_ids
                if x.event_type in ("open", "delivered")
            ]
            if dates:
                mail.email_read = max(dates)

    def _inverse_email_read(self):
        return True

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def send_unread_b2s(self):
        """
        IR Action Rule called 3 days after correspondence is sent
        by e-mail. It will create a new communication to send it by post
        if the email is not read.
        :return: True
        """
        unread_config = self.env.ref(
            "partner_communication_compassion.child_letter_unread"
        )
        for letter in self:
            if letter.communication_id.filter_not_read():
                self.env["partner.communication.job"].create(
                    {
                        "partner_id": letter.partner_id.id,
                        "config_id": unread_config.id,
                        "object_ids": letter.id,
                    }
                )
        return True
