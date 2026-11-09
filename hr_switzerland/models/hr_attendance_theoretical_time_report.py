##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models


class HrAttendanceTheoreticalTimeReport(models.Model):
    _inherit = "hr.attendance.theoretical.time.report"

    def _from_sub1(self):
        """Add the extra hours removed by an allocation (e.g. paid extra hours)
        to the report, as negative worked hours on the allocation date, so that
        the report balance follows the Odoo extra hours balance.
        Other adjustments (e.g. initial balance) are not related to the report.
        """
        return """
            (
                SELECT id, employee_id, check_in, leave_hours, active,
                       worked_hours, theoretical_hours
                FROM hr_attendance
                UNION ALL
                SELECT -ot.id, ot.employee_id, ot.date::timestamp, 0.0, TRUE,
                       ot.duration, 0.0
                FROM hr_attendance_overtime ot
                JOIN hr_leave_allocation hla ON hla.overtime_id = ot.id
                WHERE ot.adjustment
            ) ha
            LEFT JOIN hr_employee AS hahe ON ha.employee_id = hahe.id
            """
