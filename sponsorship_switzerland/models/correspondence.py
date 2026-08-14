##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Samy Bucher <samy.bucher@outlook.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, fields, models


class Correspondence(models.Model):
    _inherit = "correspondence"

    gift_id = fields.Many2one(
        "sponsorship.gift",
        "Gift",
        compute="_compute_gift",
        store=True,
        help="Gift the child is thanking for. Either confirmed by GMC or, "
        "when GMC did not give us the information, estimated with the last "
        "gift delivered for this sponsorship.",
    )
    gift_source = fields.Selection(
        [("verified", "Confirmed by GMC"), ("estimated", "Estimated")],
        compute="_compute_gift",
        store=True,
    )
    verified_gift_id = fields.Many2one(
        "sponsorship.gift",
        "Gift confirmed by GMC",
        readonly=True,
        copy=False,
        help="Set when the link with the gift was imported from a GMC file.",
    )

    @api.depends(
        "verified_gift_id",
        "state",
        "communication_type_ids",
        "sponsorship_id",
        "scanned_date",
    )
    def _compute_gift(self):
        estimations = self._estimate_gifts()
        for letter in self:
            verified_gift = letter.verified_gift_id
            gift = verified_gift or estimations.get(letter.id)
            letter.gift_id = gift
            if not gift:
                letter.gift_source = False
            else:
                letter.gift_source = "verified" if verified_gift else "estimated"

    def _estimate_gifts(self):
        """Guess the gift of each letter with the last gift that was delivered
        before the letter was scanned.
        :return: dictionary mapping letter id to a sponsorship.gift record
        """
        gift_types = self.env.ref(
            "sbc_compassion.correspondence_type_large_gift"
        ) + self.env.ref("sbc_compassion.correspondence_type_small_gift")
        letters = self.filtered(
            lambda letter: not letter.verified_gift_id
            and letter.scanned_date
            and letter.state == "Published to Global Partner"
            and letter.communication_type_ids & gift_types
        )
        if not letters:
            return {}
        # Gifts are ordered by gift_date desc, so the first match of each
        # sponsorship is the last gift made before the letter was scanned.
        gifts_per_sponsorship = (
            self.env["sponsorship.gift"]
            .search(
                [
                    ("sponsorship_id", "in", letters.sponsorship_id.ids),
                    ("state", "=", "Delivered"),
                    ("status_change_date", "<", max(letters.mapped("scanned_date"))),
                ]
            )
            .grouped("sponsorship_id")
        )
        return {
            letter.id: next(
                (
                    gift
                    for gift in gifts_per_sponsorship.get(letter.sponsorship_id, [])
                    if gift.status_change_date.date() < letter.scanned_date
                ),
                False,
            )
            for letter in letters
        }
