# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nathan Fluckiger <nathan.fluckiger@hotmail.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, api


class EventCompassion(models.Model):

    _inherit = 'crm.event.compassion'

    @api.model
    def create(self, vals):
        event = super(EventCompassion, self).create(vals)
        for NewEvent in self:
            if NewEvent.campaign_id is not None:
                NewEvent.analytic_id.campaign_id = NewEvent.campaign_id
        return event

    @api.multi
    def write(self, vals):
        event = super(EventCompassion, self).write(vals)
        for NewEvent in self:
            if NewEvent.campaign_id is not None:
                NewEvent.analytic_id.campaign_id = NewEvent.campaign_id
        return event
