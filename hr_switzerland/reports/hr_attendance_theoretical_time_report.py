# Copyright 2017-2019 Tecnativa - Pedro M. Baeza
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from psycopg2.extensions import AsIs

from odoo import api, models, tools


class HrAttendanceTheoreticalTimeReport(models.Model):
    _inherit = "hr.attendance.theoretical.time.report"

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            """
            CREATE OR REPLACE VIEW %s AS (
            WITH daily_leave_hours AS (
                SELECT hl.employee_id,
                       d.date,
                       case when hl.number_of_days > 1
                              then rc.hours_per_day
                            else rc.hours_per_day * hl.number_of_days
                       end as leave_hours
                  FROM hr_leave hl
                 CROSS JOIN generate_series(
                 (hl.date_from AT TIME ZONE 'UTC' AT TIME ZONE
                 'Europe/Zurich')::date,
                 (hl.date_to AT TIME ZONE 'UTC' AT TIME ZONE
                 'Europe/Zurich')::date,
                  '1 day'::interval
                                            ) AS d(date)
                 JOIN hr_employee_calendar hec
                   ON hec.employee_id = hl.employee_id
                  AND d.date BETWEEN hec.date_start
                  AND COALESCE(hec.date_end, '9999-12-31')
                 JOIN resource_calendar rc
                   ON rc.id = hec.calendar_id
                 WHERE hl.state = 'validate'
                   AND EXTRACT(isodow FROM d.date) < 6
                   AND NOT EXISTS (SELECT 1
                                     FROM hr_holidays_public_line hhpl
                                    WHERE hhpl.date = d.date
                                  )
                 GROUP BY hl.employee_id,
                          d.date,
                          hl.number_of_days,
                          rc.hours_per_day
            ),
            daily_theoretical_hours AS (
                WITH daily_schedule_rules AS (
                    SELECT he.id as employee_id,
                           hec.date_start,
                           COALESCE(hec.date_end, '9999-12-31') as date_end,
                           rca.dayofweek,
                           rca.hour_from,
                           rca.hour_to
                      FROM hr_employee he
                      JOIN hr_employee_calendar hec
                        ON hec.employee_id = he.id
                      JOIN resource_calendar_attendance rca
                        ON rca.calendar_id = hec.calendar_id
                ),
                working_days_hours AS (
                    SELECT rules.employee_id,
                           all_days.date,
                           (rules.hour_to - rules.hour_from) as work_duration
                      FROM daily_schedule_rules rules
                      JOIN generate_series( (SELECT MIN(date_start)
                                               FROM daily_schedule_rules),
                                                    CURRENT_DATE,
                                                    '1 day'::interval
                                        ) AS all_days(date)
                        ON all_days.date BETWEEN rules.date_start
                       AND rules.date_end
                    AND EXTRACT(isodow FROM all_days.date) = (rules.dayofweek::int + 1)
                )
                SELECT wdh.employee_id,
                       wdh.date,
                       SUM(wdh.work_duration) AS theoretical_hours
                  FROM working_days_hours wdh
                 WHERE NOT EXISTS (SELECT 1
                                     FROM hr_holidays_public_line hhpl
                                    WHERE hhpl.date = wdh.date
                                  )
                 GROUP BY wdh.employee_id,
                          wdh.date
            ),
            daily_worked_hours AS (
                SELECT ha.employee_id,
                       ha.check_in::date AS date,
                       SUM(ha.worked_hours) AS worked_hours
                  FROM hr_attendance ha
                 WHERE ha.employee_id IS NOT NULL
                 GROUP BY ha.employee_id,
                          ha.check_in::date
            ),

            unioned_data AS (
                SELECT employee_id,
                       date,
                       theoretical_hours,
                       0 as worked_hours,
                       0 as personal_leave_hours
                  FROM daily_theoretical_hours
                UNION ALL
                SELECT employee_id,
                       date,
                       0 as theoretical_hours,
                       worked_hours,
                       0 as personal_leave_hours
                  FROM daily_worked_hours
                UNION ALL
                SELECT employee_id,
                       date,
                       0 as theoretical_hours,
                       0 as worked_hours,
                       leave_hours as personal_leave_hours
                  FROM daily_leave_hours
            )
            SELECT ROW_NUMBER() OVER() AS id,
                   ud.employee_id,
                   he.department_id,
                   ud.date,
                   SUM(ud.worked_hours) as worked_hours,
                   CASE WHEN SUM(ud.theoretical_hours) > 0
                          THEN SUM(ud.theoretical_hours) - SUM(ud.personal_leave_hours)
                        ELSE 0
                   END as theoretical_hours,
                   CASE WHEN SUM(ud.theoretical_hours) > 0
                   THEN (SUM(ud.worked_hours) + SUM(ud.personal_leave_hours) -
                   SUM(ud.theoretical_hours))
                        ELSE SUM(ud.worked_hours)
                   END as difference
              FROM unioned_data ud
              JOIN hr_employee he ON ud.employee_id = he.id
             where ud.theoretical_hours <> 0
                or ud.worked_hours <> 0
                or ud.personal_leave_hours <> 0
             GROUP BY ud.employee_id,
                      he.department_id,
                      ud.date
        )""",
            (AsIs(self._table),),
        )

    @api.model
    def read_group(
        self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True
    ):
        return models.Model.read_group(
            self,
            domain,
            fields,
            groupby,
            offset=offset,
            limit=limit,
            orderby=orderby,
            lazy=lazy,
        )
