from datetime import date

from odoo.tests import TransactionCase


class TestPaidExtraHours(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        attendances = []
        for day in "01234":
            for period, hour_from, hour_to in (
                ("morning", 8, 12),
                ("afternoon", 13, 17),
            ):
                attendances.append(
                    (
                        0,
                        0,
                        {
                            "name": f"{day} {period}",
                            "dayofweek": day,
                            "day_period": period,
                            "hour_from": hour_from,
                            "hour_to": hour_to,
                            "date_from": date(2020, 1, 1),
                        },
                    )
                )
        cls.calendar = cls.env["resource.calendar"].create(
            {"name": "Dated calendar", "attendance_ids": attendances}
        )
        cls.employee = cls.env["hr.employee"].create(
            {"name": "Overtime Employee", "resource_calendar_id": cls.calendar.id}
        )
        cls.paid_type = cls.env["hr.leave.type"].create(
            {
                "name": "Paid Extra Hours",
                "requires_allocation": "yes",
                "employee_requests": "no",
                "overtime_deductible": True,
                "request_unit": "hour",
            }
        )

    def test_hours_per_day_dated_calendar(self):
        """A calendar with only dated attendances has its hours per day."""
        self.assertEqual(self.calendar.stored_hours_per_day, 8)

    def test_paid_extra_hours_in_report(self):
        """Extra hours removed by an allocation are in the theoretical report,
        other adjustments are not."""
        report = self.env["hr.attendance.theoretical.time.report"]
        self.env["hr.attendance.overtime"].create(
            {
                "employee_id": self.employee.id,
                "date": date(2024, 6, 30),
                "adjustment": True,
                "duration": 20,
            }
        )
        allocation = self.env["hr.leave.allocation"].create(
            {
                "name": "Paid",
                "employee_id": self.employee.id,
                "holiday_status_id": self.paid_type.id,
                "number_of_days": 5 / 8,
                "date_from": date(2026, 10, 31),
            }
        )
        self.assertEqual(allocation.number_of_hours_display, 5)
        self.assertEqual(allocation.overtime_id.duration, -5)
        self.assertEqual(self.employee.total_overtime, 15)
        self.env.flush_all()
        lines = report.search([("employee_id", "=", self.employee.id)])
        self.assertEqual(lines.date, date(2026, 10, 31))
        self.assertEqual(sum(lines.mapped("difference")), -5)

    def test_negative_extra_hours_in_my_time(self):
        """The extra hours card is shown in "My Time" with a negative balance."""
        extra_type = self.env["hr.leave.type"].create(
            {
                "name": "Extra Hours",
                "requires_allocation": "no",
                "overtime_deductible": True,
                "request_unit": "hour",
            }
        )
        self.env["hr.attendance.overtime"].create(
            {
                "employee_id": self.employee.id,
                "date": date(2026, 1, 1),
                "adjustment": True,
                "duration": -3,
            }
        )
        data = extra_type.get_allocation_data(self.employee)[self.employee]
        cards = [card for card in data if card[3] == extra_type.id]
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0][1]["virtual_remaining_leaves"], -3)
