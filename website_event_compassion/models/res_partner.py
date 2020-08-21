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
    )

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    def write(self, vals):
        super().write(vals)
        if vals.get("criminal_record"):
            self.mapped("registration_ids").write({
                "completed_task_ids": [(4, self.env.ref(
                    "website_event_compassion.task_criminal").id)]
            })
        return True
