##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    registration_ids = fields.One2many(
        "event.registration", "partner_id", "Event registrations", readonly=False,
        inverse="_inverse_criminal_record"
    )

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    def _inverse_criminal_record(self):
        super()._inverse_criminal_record()
        attachment_obj = self.env["ir.attachment"].sudo()
        for partner in self:
            criminal_record = partner.criminal_record
            if criminal_record:
                # search for all registrations and write completed task
                for registration in self.registration_ids:
                    if registration:
                        registration.write(
                            {
                                "completed_task_ids": [
                                    (
                                        4,
                                        registration.env.ref(
                                            "website_event_compassion.task_criminal"
                                        ).id,
                                    ),
                                ]
                            }
                        )

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def notify_criminal_record_expiration(self):
        """
        Action rule called when a criminal record expires. A notification is sent
        to the responsible defined in Compassion Settings.
        """
        # search for responsible of criminal record expiration in settings
        notify_ids = (
            self.env["res.config.settings"].sudo().get_param(
                "criminal_record_expiration_ids")
        )
        # send notifications
        if notify_ids:
            for user_id in notify_ids[0][2]:
                for partner in self:
                    partner.activity_schedule(
                        "mail.mail_activity_data_warning",
                        summary=_("A criminal record is expiring today"),
                        note=_("The criminal record of {} expires today.".
                               format(partner.name)
                               ),
                        user_id=user_id
                    )
