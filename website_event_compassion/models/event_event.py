# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields


class Event(models.Model):
    _inherit = 'event.event'

    compassion_event_id = fields.Many2one(
        'crm.event.compassion', 'Event')
    wordpress_url = fields.Char(translate=True)
    total_price = fields.Float(compute='_compute_total_price')

    def _compute_total_price(self):
        for event in self:
            event.total_price = sum(
                event.mapped('event_ticket_ids.price') or [0])
