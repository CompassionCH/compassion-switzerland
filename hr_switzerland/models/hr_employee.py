##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Stephane Eicher <seicher@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields


class HrEmployee(models.AbstractModel):
    _inherit = "hr.employee.base"

    job_title = fields.Char(translate=True)

    def _attendance_action_change(self):
        """Change the state of the employee to show if he's online or not"""
        if self.attendance_state != "checked_in":
            self.env.user.asterisk_connect(True)
        else:
            self.env.user.asterisk_connect(False)

        return super()._attendance_action_change()
