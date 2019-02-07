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


class EventType(models.Model):
    # Inherit from 'mail.thread' so that the followers can be notified when
    # events of the type have changed.
    _inherit = ['event.type', 'mail.thread']
    _name = 'event.type'

    accepts_registrations = fields.Boolean(default=True)
    travel_features = fields.Boolean(
        help='Use this to activate the travel registration features'
    )
