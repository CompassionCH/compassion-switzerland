from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    bank_account = fields.Many2one(
        "res.partner.bank",
        string="Bank Account",
        help="Bank account to be used for the QR-bill.",
    )

    def print_ch_qr_bill(self):
        """Triggered by the 'Print QR-bill' button."""
        self.ensure_one()

        if not self.partner_bank_id._eligible_for_qr_code(
            "ch_qr", self.partner_id, self.currency_id
        ):
            raise UserError(
                _(
                    "Cannot generate the QR-bill. Please check you have configured the "
                    "address of your company and debtor. If you are using a QR-IBAN, "
                    "also check the invoice's payment reference is a QR reference."
                )
            )

        self.l10n_ch_isr_sent = True
        # self.bank_account = self.partner_bank_id
        self.write({"bank_account": self.partner_bank_id.id})
        return self.env.ref("report_compassion.report_compassion_qr").report_action(
            self
        )
