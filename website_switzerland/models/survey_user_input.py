##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models


class SurveyUserInput(models.Model):
    _inherit = "survey.user_input"

    def write(self, vals):
        """
        Automatically complete Medical Survey task when user filled it
        """
        res = super().write(vals)
        if vals.get("state") == "done":
            # Search for Group Visit medical surveys
            registrations = (
                self.env["event.registration"]
                .sudo()
                .search(
                    [
                        ("partner_id", "in", self.mapped("partner_id").ids),
                        (
                            "event_id.event_type_id",
                            "=",
                            self.env.ref(
                                "website_switzerland.event_type_group_visit"
                            ).id,
                        ),
                        (
                            "stage_id",
                            "=",
                            self.env.ref("website_switzerland.stage_group_medical").id,
                        ),
                    ]
                )
            )
            task_medical = self.env.ref("website_switzerland.task_medical_survey")
            registrations.mapped("task_ids").filtered(
                lambda t: t.task_id == task_medical
            ).write({"done": True})
        return res
