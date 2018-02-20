# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Marco Monzione
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import math

from datetime import datetime

from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    extra_hours_formatted = fields.Char(string="Balance",
                                   compute='_compute_extra_hours')

    time_warning_balance = fields.Char(compute='_compute_time_warning_balance')

    time_warning_today = fields.Char(compute='_compute_time_warning_today')

    extra_hours_today = fields.Char(compute='_compute_extra_hours_today')

    today_hour = fields.Char(compute='_compute_today_hour')

    def _compute_extra_hours_today(self):
        for employee in self:
            today_hour = employee._today_hour() - 8

            employee.extra_hours_today = '- ' if today_hour < 0 else '+'
            employee.extra_hours_today += employee.\
                _convert_hour_to_time(today_hour)

    def _compute_time_warning_balance(self):
        for employee in self:
            if employee.extra_hours < 0:
                employee.time_warning_balance = 'red'
            elif employee.extra_hours >= 19:
                employee.time_warning_balance = 'orange'
            else:
                employee.time_warning_balance = 'green'

    def _compute_time_warning_today(self):
        for employee in self:
            employee.time_warning_today = 'red' if employee._today_hour() < \
                8 else 'green'

    def _compute_today_hour(self):
        for employee in self:
            employee.today_hour = employee._convert_hour_to_time(
                employee._today_hour())

    def _compute_extra_hours(self):
        for employee in self:
            employee.extra_hours_formatted = '-' if employee.extra_hours < 0 else ''
            employee.extra_hours_formatted += \
                employee._convert_hour_to_time(math.fabs(employee.extra_hours))

    def _convert_hour_to_time(self, hour):
        return '{:02d}:{:02d}'.format(*divmod(int(math.fabs(hour*60)), 60))

    def _today_hour(self):
        self.ensure_one()
        today = fields.Date.today()
        attendances_today = self.env['hr.attendance'].search([
            ('employee_id', '=', self.id),
            ('check_in', '>=', today)
        ])
        worked_hours = 0
        for attendance in attendances_today:
            if attendance.check_out:
                worked_hours += attendance.worked_hours
            else:
                delta = datetime.now() - fields.Datetime.from_string(
                    attendance.check_in)
                worked_hours += delta.total_seconds() / 3600.0
        return worked_hours
