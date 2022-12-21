##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Steve Ferry
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, _


# pylint: disable=C8107
class ResPartnerBank(models.Model):
    """ This class upgrade the partners.bank to match Compassion needs.
    """

    _inherit = "res.partner.bank"

    def build_swiss_code_vals(self, amount, *args):
        """In l10n_ch's build_swiss_code_vals the amount must be a number
        and can't be empty to be allowed in post offices.
        This function is a workaround to this problem.
        We also ensure that the amount is in the range specified by the swiss qr specifications.
        """
        must_be_corrected = type(amount) not in [int, float] or not (0.01 <= amount <= 999999999.99)
        if not must_be_corrected:
            return super().build_swiss_code_vals(amount, *args)

        amount = -3141592.64 # dummy value
        qr_code_vals = super().build_swiss_code_vals(amount, *args)
        # ensure that this position is still the amount
        assert qr_code_vals[18] == f"{amount:.2f}"
        qr_code_vals[18] = ""
        return qr_code_vals

    def validate_swiss_code_arguments(self, currency, debtor_partner, reference_to_check=''):
        """Override this function to let the creation of QR invoices without partner's information
           As we can have partners without an address set we get rid of the inner function _partner_fields_set.
        """
        return (reference_to_check == '' or not self._is_qr_iban()
                or self._is_qr_reference(reference_to_check))


    @api.model
    def create(self, data):
        """Override function to notify creation in a message
        """
        result = super().create(data)

        part = result.partner_id
        if part:
            part.message_post(
                body=_("<b>Account number: </b>" + result.acc_number),
                subject=_("New account created"),
                type="comment",
            )

        return result

    @api.multi
    def unlink(self):
        """Override function to notify delte in a message
        """
        for account in self:
            part = account.partner_id
            part.message_post(
                body=_("<b>Account number: </b>" + account.acc_number),
                subject=_("Account deleted"),
                type="comment",
            )

        result = super().unlink()
        return result
