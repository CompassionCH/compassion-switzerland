##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Joel Vaucher <jvaucher@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import re

from odoo import _, api, fields, models


class SearchBankAddressWizard(models.TransientModel):
    _name = "search.bank.address.wizard"
    _description = "Wizard search bank address"

    move_id = fields.Many2one(
        "account.move",
        domain=lambda self: self._get_domain(),
        default=lambda self: self._get_default(),
    )
    partner_address = fields.Text(
        "Partner Address",
        compute="_compute_partner_address",
        readonly=True,
    )
    date = fields.Date(
        "Last time used",
        related="move_id.date",
    )

    overwriting_street = fields.Char("Street", default="")
    overwriting_zip_id = fields.Many2one("res.city.zip", "City/Location")

    def _get_domain(self):
        partner_id = self.env.context.get("active_id")
        # Check in camt_parser from OCA (puts the address read in narration)
        narration_txt = _("Postal Address")
        if partner_id:
            return [
                ("partner_id", "=", partner_id),
                ("narration", "like", narration_txt),
            ]
        return []

    def _get_default(self):
        return self.env["account.move"].search(
            self._get_domain(), order="date desc", limit=1
        )

    def _extract_address_from_narration(self, narration):
        """
        Extract Postal Address from move_id.narration field
        """
        match = re.search(r"Postal Address\s*\(PstlAdr\):\s*(.*)", narration)
        if match:
            return match.group(1).strip()
        return ""

    @api.depends("move_id.narration")
    def _compute_partner_address(self):
        for record in self:
            narration = record.move_id.narration or ""
            record.partner_address = self._extract_address_from_narration(narration)

    def change_address(self):
        self.env["res.partner"].browse(self.env.context["active_id"]).write(
            {
                "street": self.overwriting_street,
                "country_id": self.overwriting_zip_id.city_id.country_id.id,
                "state_id": self.overwriting_zip_id.city_id.state_id.id,
                "city_id": self.overwriting_zip_id.city_id.id,
                "city": self.overwriting_zip_id.city_id.name,
                "zip_id": self.overwriting_zip_id.id,
                "zip": self.overwriting_zip_id.name,
            }
        )
        return {"type": "ir.actions.act_window_close"}

    def cancel_change(self):
        return {"type": "ir.actions.act_window_close"}
