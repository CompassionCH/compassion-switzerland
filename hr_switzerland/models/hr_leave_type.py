##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models


class HrLeaveType(models.Model):
    _inherit = "hr.leave.type"

    def get_allocation_data(self, employees, date=None):
        """Show the extra hours card in "My Time" also when the balance is
        negative (hr_holidays_attendance only shows a positive balance)."""
        res = super().get_allocation_data(employees, date)
        deductible_types = self.env["hr.leave.type"].search(
            [("overtime_deductible", "=", True), ("requires_allocation", "=", "no")]
        )
        for employee in employees:
            overtime = employee.sudo().total_overtime
            if overtime >= 0:
                continue
            for leave_type in deductible_types & self:
                res[employee].append(
                    (
                        leave_type.name,
                        {
                            "remaining_leaves": 0,
                            "virtual_remaining_leaves": overtime,
                            "max_leaves": overtime,
                            "leaves_taken": 0,
                            "virtual_leaves_taken": 0,
                            "closest_allocation_remaining": 0,
                            "closest_allocation_expire": False,
                            "total_virtual_excess": 0,
                            "virtual_excess_data": {},
                            "request_unit": leave_type.request_unit,
                            "icon": leave_type.sudo().icon_id.url,
                            "allows_negative": leave_type.allows_negative,
                            "max_allowed_negative": leave_type.max_allowed_negative,
                            "overtime_deductible": True,
                        },
                        leave_type.requires_allocation,
                        leave_type.id,
                    )
                )
        return res
