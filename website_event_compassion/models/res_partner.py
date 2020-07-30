##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields


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
