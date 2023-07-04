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
    """This class upgrade the partners.bank to match Compassion needs."""

    _inherit = "res.partner.bank"

    def build_swiss_code_vals(self, amount, *args):
        """In l10n_ch's build_swiss_code_vals the amount must be a number
        and can't be empty to be allowed in post offices.
        This function is a workaround to this problem.
        We also ensure that the amount is in the range specified by the swiss qr specifications.
        Furthermore, when the debtor partner isn't set correctly, we do not declare its information in the QR
        to avoid errors on the user e-banking side.
        """
        qr_code_vals = super().build_swiss_code_vals(amount, *args)

        must_be_corrected = type(amount) not in [int, float] or not (
            0.01 <= amount <= 999999999.99
        )

        if must_be_corrected:
            amount = -3141592.64  # dummy value
            qr_code_vals = super().build_swiss_code_vals(amount, *args)
            # ensure that this position is still the amount
            assert qr_code_vals[18] == f"{amount:.2f}"
            qr_code_vals[18] = ""

        # Set the debtor's value as nothing to escape scanning errors when the debtors information is not set correctly
        if False in [args[2].city, args[2].zip, args[2].country_id.code]:
            qr_code_vals[20] = ""  # Ultimate Debtor Address Type
            qr_code_vals[21] = ""  # Ultimate Debtor Name
            qr_code_vals[22] = ""  # Ultimate Debtor Address Line 1
            qr_code_vals[23] = ""  # Ultimate Debtor Address Line 2
            qr_code_vals[26] = ""  # Ultimate Debtor Postal Country

        return qr_code_vals

    def validate_swiss_code_arguments(
        self, currency, debtor_partner, reference_to_check=""
    ):
        """Override this function to let the creation of QR invoices without partner's information
        As we can have partners without an address set we get rid of the inner function _partner_fields_set.
        """
        return (
            reference_to_check == ""
            or not self._is_qr_iban()
            or self._is_qr_reference(reference_to_check)
        )

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

    @api.model_create_multi
    def create(self, data):
        """Override function to notify creation in a message"""
        result = super().create(data)
        for bank in result:
            if bank.partner_id:
                bank.message_post(
                    body=_("<b>Account number: </b>" + bank.acc_number),
                    subject=_("New account created"),
                    type="comment",
                )
        return result

    def unlink(self):
        """Override function to notify delte in a message"""
        for account in self:
            part = account.partner_id
            part.message_post(
                body=_("<b>Account number: </b>" + account.acc_number),
                subject=_("Account deleted"),
                type="comment",
            )

        result = super().unlink()
        return result
