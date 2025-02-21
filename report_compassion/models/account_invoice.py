import re

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.float_utils import float_split_str
from odoo.tools.misc import mod10r

class AccountMove(models.Model):
    _inherit = 'account.move'

    bank_account = fields.Many2one()

    def print_ch_qr_bill(self):
        """ Triggered by the 'Print QR-bill' button.
        """
        self.ensure_one()

        if not self.partner_bank_id._eligible_for_qr_code('ch_qr', self.partner_id, self.currency_id):
            raise UserError(_("Cannot generate the QR-bill. Please check you have configured the address of your company and debtor. If you are using a QR-IBAN, also check the invoice's payment reference is a QR reference."))

        self.l10n_ch_isr_sent = True
        # self.bank_account = self.partner_bank_id
        # return self.env.ref('report_compassion.report_compassion_qr').report_action(self)
        return self.env.ref('report_compassion.report_compassion_qr_parent').report_action(self)