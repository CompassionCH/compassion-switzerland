# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields, api


class MuskathlonDetails(models.Model):
    _inherit = "advocate.details"

    emergency_name = fields.Char('Emergency contact name')
    emergency_phone = fields.Char('Emergency contact phone number')
    emergency_relation_type = fields.Selection([
        ('husband', 'Husband'),
        ('wife', 'Wife'),
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('brother', 'Brother'),
        ('sister', 'Sister'),
        ('son', 'Son'),
        ('daughter', 'Daughter'),
        ('friend', 'Friend'),
        ('other', 'Other')
    ], string='Emergency contact relation type')
    birth_name = fields.Char()
    passport_number = fields.Char()
    passport_expiration_date = fields.Date()
    trip_information_complete = fields.Boolean(
        compute='_compute_trip_information_complete'
    )

    sql_constraints = [
        ('partner_unique', 'UNIQUE (partner_id)', 'Partner must be unique.')
    ]

    @api.multi
    def _compute_trip_information_complete(self):
        for record in self:
            trip_info = [
                record.emergency_name, record.emergency_phone,
                record.emergency_relation_type, record.t_shirt_size,
                record.passport_number, record.passport_expiration_date,
                record.birth_name
            ]
            for info in trip_info:
                if not info:
                    record.trip_information_complete = False
                    break
            else:
                record.trip_information_complete = True
