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
        event = super().create(vals)
        if event.campaign_id:
            event.analytic_id.campaign_id = event.campaign_id
            event.origin_id.campaign_id = event.campaign_id
        return event

    @api.multi
    def write(self, vals):
        res = super().write(vals)
        for new_event in self:
            if new_event.campaign_id:
                new_event.analytic_id.campaign_id = new_event.campaign_id
                new_event.origin_id.campaign_id = new_event.campaign_id
        return res
