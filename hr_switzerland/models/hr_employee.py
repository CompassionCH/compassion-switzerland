##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Stephane Eicher <seicher@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, api, fields


class HrEmployee(models.Model):
    _inherit = "hr.employee"
    _description = "Employee"

    job_title = fields.Char(translate=True)

    def attendance_action_change(self):
        """Change the state of the employee to show if he's online or not"""
        for employee in self:
            if employee.attendance_state != "checked_in":
                employee.env.user.asterisk_connect(True)
            else:
                employee.env.user.asterisk_connect(False)

        return super().attendance_action_change()
