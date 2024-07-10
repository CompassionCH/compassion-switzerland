##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Steve Ferry
#    @author: Noé Berdoz <nberdoz@compasion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import _, models


# pylint: disable=C8107
class ResPartnerBank(models.Model):
    """This class upgrade the partners.bank to match Compassion needs."""

    _inherit = "res.partner.bank"

    def _l10n_ch_get_qr_vals(
        self,
        amount,
        currency_name,
        debtor_partner,
        free_communication,
        structured_communication,
    ):
        """
        Returns a list of values for a Swiss QR bill.
        Allows invoices with no amount to let the payer choose the amount to pay.
        """
        qr_vals = super()._l10n_ch_get_qr_vals(
            amount,
            currency_name,
            debtor_partner,
            free_communication,
            structured_communication,
        )
        # Set amount to an empty string indicating that it has to be chosen by the payer
        qr_vals[18] = "" if qr_vals[18] == "0.00" else qr_vals[18]

        return qr_vals

    def _get_partner_address_lines(self, partner):
        """Override to allow empty zip or city."""
        line_1 = (
            (partner and partner.street or "")
            + " "
            + (partner and partner.street2 or "")
        )
        line_2 = (
            (partner and partner.zip or "") + " " + (partner and partner.city or "")
        )
        return line_1[:70], line_2[:70]

    def _eligible_for_qr_code(self, qr_method, debtor_partner, currency):
        # Always allow QR-generation
        if qr_method == "ch_qr":
            return True
        return super()._eligible_for_qr_code(qr_method, debtor_partner, currency)

    def _check_for_qr_code_errors(
        self,
        qr_method,
        amount,
        currency,
        debtor_partner,
        free_communication,
        structured_communication,
    ):
        # Don't check missing addresses
        if qr_method == "ch_qr":
            if self._is_qr_iban() and not self._is_qr_reference(
                structured_communication
            ):
                return _(
                    "When using a QR-IBAN as the destination account of "
                    "a QR-code, the payment reference must be a "
                    "QR-reference."
                )
            else:
                return ""
        return super()._check_for_qr_code_errors(
            qr_method,
            amount,
            currency,
            debtor_partner,
            free_communication,
            structured_communication,
        )

    def unlink(self):
        """Override function to notify delete in a message"""
        for account in self:
            part = account.partner_id
            part.message_post(
                body=_("<b>Account number: </b>" + account.acc_number),
                subject=_("Account deleted"),
            )

        result = super().unlink()
        return result
