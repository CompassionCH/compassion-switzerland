# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Fluckiger Nathan <nathan.fluckiger@hotmail.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, fields, models


class PartnerCheckDouble(models.TransientModel):
    _name = "res.partner.check.double"

    partner_id = fields.Many2one('res.partner')
    mergeable_partner_ids = fields.Many2many(
        'res.partner', related='partner_id.partner_duplicate_ids')
    selected_merge_partner_id = fields.Many2one('res.partner', 'Merge with')

    @api.multi
    def merge_with(self):
        self.selected_merge_partner_id.write(self.partner_id.read([
            'phone', 'mobile', 'email', 'street', 'street2', 'street3',
            'city', 'zip', 'preferred_name'])[0])
        self.partner_id.unlink()
        return {
            "type": "ir.actions.act_window",
            "res_model": "res.partner",
            "views": [[None, "form"]],
            "res_id": self.selected_merge_partner_id.id,
            "target": "main",
        }

    @api.multi
    def keep(self):
        self.partner_id.partner_duplicate_ids = False
        return True
