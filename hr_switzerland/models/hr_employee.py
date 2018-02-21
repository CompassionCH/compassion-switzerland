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

from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    extra_hours_formatted = fields.Char(string="Balance",
                                   compute='_compute_extra_hours')

    time_warning_balance = fields.Char(compute='_compute_time_warning_balance')

    time_warning_today = fields.Char(compute='_compute_time_warning_today')

    extra_hours_today = fields.Char(compute='_compute_extra_hours_today')

    today_hour = fields.Char(compute='_compute_today_hour')

    today_hour_formatted = fields.Char(compute='_compute_today_hour_formatted')

    @api.multi
    @api.depends('today_hour')
    def _compute_extra_hours_today(self):
        for employee in self:
            employee.extra_hours_today = \
                '- ' if employee.today_hour < 0 else '+'
            employee.extra_hours_today += employee.\
                _convert_hour_to_time(employee.today_hour)

    @api.multi
    def _compute_time_warning_balance(self):
        for employee in self:
            if employee.extra_hours < 0:
                employee.time_warning_balance = 'red'
            elif employee.extra_hours >= 19:
                employee.time_warning_balance = 'orange'
            else:
                employee.time_warning_balance = 'green'

    @api.multi
    @api.depends('today_hour')
    def _compute_time_warning_today(self):
        for employee in self:
            employee.time_warning_today = 'red' if employee.today_hour < \
                8 else 'green'

    @api.multi
    def _compute_today_hour(self):
        for employee in self:
            current_att_day = self.env['hr.attendance.day'].search([
                ('employee_id', '=', employee.id),
                ('date', '=', fields.Date.today())])
            employee.today_hour = \
                current_att_day.worked_hours - current_att_day.due_hours

    @api.multi
    def _compute_extra_hours(self):
        for employee in self:
            employee.extra_hours_formatted = \
                '-' if employee.extra_hours < 0 else ''
            employee.extra_hours_formatted += \
                employee._convert_hour_to_time(math.fabs(employee.extra_hours))

    @api.multi
    @api.depends('today_hour')
    def _compute_today_hour_formatted(self):
        for employee in self:
            employee.today_hour_formatted = \
                employee._convert_hour_to_time(employee.today_hour)

    @api.multi
    def _convert_hour_to_time(self, hour):
        hour = float(hour)
        return '{:02d}:{:02d}'.format(*divmod(int(math.fabs(hour*60)), 60))