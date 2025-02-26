from odoo import _, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    def print_ch_qr_bill(self):
        """Triggered by the 'Print QR-bill' button."""
        self.ensure_one()
        if not self.l10n_ch_isr_number and not self.payment_reference:
            raise UserError(_("No valid ISR number found on the invoice."))
        self.l10n_ch_isr_sent = True
        return self.env.ref("report_compassion.report_compassion_qr").report_action(
            self
        )
