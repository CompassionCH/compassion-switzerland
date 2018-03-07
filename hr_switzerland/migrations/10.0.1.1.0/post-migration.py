# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Sebastien Toth <popod@me.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from datetime import date, timedelta

from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # Search employees that worked since the beginning of the year
    begin_date = date(2018, 1, 1)
    attendances = env['hr.attendance'].search([
        ('check_in', '>=', begin_date.strftime('%Y-%m-%d'))
    ])
    employees = attendances.mapped('employee_id')

    # create daily report for each employee from 01.01.2018
    today = date.today()
    delta = today - begin_date
    for employee in employees:
        # https://stackoverflow.com/a/7274316
        for i in range(delta.days + 1):
            # create daily report for report_date
            report_date = begin_date + timedelta(days=i)

            env['hr.attendance.day'].create({
                'date': report_date,
                'employee_id': employee.id
            })
