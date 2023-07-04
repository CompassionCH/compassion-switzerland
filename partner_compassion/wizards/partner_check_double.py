##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Fluckiger Nathan <nathan.fluckiger@hotmail.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models


class PartnerCheckDouble(models.TransientModel):
    _name = "res.partner.check.double"
    _description = "Partner Check Duplicates"

    partner_id = fields.Many2one("res.partner", readonly=False)
    mergeable_partner_ids = fields.Many2many(
        "res.partner", related="partner_id.partner_duplicate_ids", readonly=False
    )
    selected_merge_partner_id = fields.Many2one(
        "res.partner", "Merge with", readonly=False
    )

    def merge_with(self):
        # Use base.partner.merge wizard
        self.env["base.partner.merge.automatic.wizard"].create(
            {
                "partner_ids": [
                    (6, 0, (self.partner_id + self.mergeable_partner_ids).ids)
                ],
                "dst_partner_id": self.selected_merge_partner_id.id,
            }
        ).action_merge()
        self.selected_merge_partner_id.partner_duplicate_ids = False
        return {
            "type": "ir.actions.act_window",
            "res_model": "res.partner",
            "view_mode": "form",
            "res_id": self.selected_merge_partner_id.id,
            "target": "main",
        }

    def keep(self):
        self.partner_id.partner_duplicate_ids = False
        return True
