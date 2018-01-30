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
from datetime import datetime

import math

from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    bonus_malus_hour = fields.Char(string="Bonus/Malus",
                                   compute='_compute_bonus_malus_hour')

    time_warning_balance = fields.Char(compute='_compute_time_warning_balance')

    time_warning_today = fields.Char(compute='_compute_time_warning_today')

    bonus_malus_today = fields.Char(compute='_compute_bonus_malus_today')

    today_hour = fields.Char(compute='_compute_today_hour')

    def _compute_bonus_malus_today(self):
        for employee in self:
            today_hour = employee._today_hour() - 8

            employee.bonus_malus_today = '- ' if today_hour < 0 else '+'
            employee.bonus_malus_today += employee.\
                _convert_hour_to_time(today_hour)

    def _compute_time_warning_balance(self):
        for employee in self:
            if employee.bonus_malus < 0:
                employee.time_warning_balance = 'red'
            elif employee.bonus_malus >= 19:
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

    def _compute_bonus_malus_hour(self):
        for employee in self:
            employee.bonus_malus_hour = '-' if employee.bonus_malus < 0 else ''
            employee.bonus_malus_hour += \
                employee._convert_hour_to_time(math.fabs(employee.bonus_malus))

    def _convert_hour_to_time(self, hour):
        return '{:02d}:{:02d}'.format(*divmod(int(math.fabs(hour*60)), 60))

    def _today_hour(self):
        return sum(self.env['hr.attendance'].search([('employee_id',
                                                      '=',
                                                      self.id)]).filtered(
            lambda i: datetime.strptime(i.create_date, "%Y-%m-%d %H:%M:%S").
            date() >= datetime.now().date()).mapped('worked_hours'))
