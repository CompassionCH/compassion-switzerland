# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Fluckiger Nathan <nathan.fluckiger@hotmail.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from odoo import api, fields, models


class PartnerCheckDouble(models.TransientModel):
    _name = "res.partner.check.double"

    newpartner_id = fields.Many2one('res.partner')
    mergeable_partner_ids = fields.Many2many(
        'res.partner', 'res_partner_check_double_relation', 'wizard_id',
        'partner_id', readonly=True, string="Similar partners found")
    selected_merge_partner_id = fields.Many2one('res.partner', 'Merge with')

    @api.multi
    def mergewith(self):
        self.selected_merge_partner_id.write(self.newpartner_id.read([
            'phone', 'mobile', 'email', 'street', 'street2', 'street3',
            'city', 'zip', 'preferred_name'])[0])
        self.newpartner_id.unlink()
        return {"type": "ir.actions.act_window",
                "res_model": "res.partner",
                "views": [[None, "form"]],
                "res_id": self.selected_merge_partner_id.id,
                "target": "main",
                }

    @api.multi
    def keep(self):
        return True
