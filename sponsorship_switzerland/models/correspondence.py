##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Samy Bucher <samy.bucher@outlook.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models


class Correspondence(models.Model):
    _inherit = "correspondence"

    gift_id = fields.Many2one("sponsorship.gift", "Last gift", compute="_compute_gift")

    def _compute_gift(self):
        gift_types = self.env.ref(
            "sbc_compassion.correspondence_type_large_gift"
        ) + self.env.ref("sbc_compassion.correspondence_type_small_gift")
        for letter in self:
            if (
                letter.state == "Published to Global Partner"
                and letter.communication_type_ids & gift_types
            ):
                letter.gift_id = self.env["sponsorship.gift"].search(
                    [
                        ("sponsorship_id", "=", letter.sponsorship_id.id),
                        ("state", "=", "Delivered"),
                        ("status_change_date", "<", letter.scanned_date),
                    ],
                    limit=1,
                )
            else:
                letter.gift_id = False
