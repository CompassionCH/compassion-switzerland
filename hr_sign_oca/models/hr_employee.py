#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    sign_request_ids = fields.One2many(
        "sign.oca.request",
        "employee_id",
        string="Sign Requests",
        groups="sign_oca.sign_oca_group_user",
    )
    sign_request_count = fields.Integer(
        compute="_compute_sign_request_count",
        groups="sign_oca.sign_oca_group_user",
    )

    def _compute_sign_request_count(self):
        counts = dict(
            self.env["sign.oca.request"]._read_group(
                [("employee_id", "in", self.ids)], ["employee_id"], ["__count"]
            )
        )
        for employee in self:
            employee.sign_request_count = counts.get(employee, 0)

    def action_view_sign_requests(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "sign_oca.sign_oca_request_act_window"
        )
        action["domain"] = [("employee_id", "=", self.id)]
        action["context"] = {"create": False}
        return action
