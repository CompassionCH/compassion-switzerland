# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields


class EventFlight(models.Model):
    _name = 'event.flight'
    _description = 'Event participant flight'
    _rec_name = 'flight_number'

    registration_id = fields.Many2one(
        'event.registration', 'Participant', required=True)
    flight_type = fields.Selection([
        ('outbound', 'Outbound flight'),
        ('return', 'Return flight'),
    ])
    flying_company = fields.Char()
    flight_number = fields.Char(required=True, index=True)
    departure = fields.Datetime(required=True)
    arrival = fields.Datetime(required=True)
