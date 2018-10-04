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
    _inherit = 'event.registration'

    compassion_event_id = fields.Many2one(
        'crm.event.compassion', related='event_id.compassion_event_id')
