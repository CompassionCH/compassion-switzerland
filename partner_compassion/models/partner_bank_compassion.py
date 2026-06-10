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
import re
from itertools import chain

from odoo import _, models

from odoo.addons.base.models.res_bank import sanitize_account_number

# Swiss Payment Standards - Swiss Implementation Guidelines for the QR-bill
# - version 2.3
UNICODE_ALLOWED = {
    chr(ucode)
    for ucode in chain(
        range(0x20, 0x80), range(0xA0, 0x180), range(0x218, 0x21C), [0x20AC]
    )
}
ADDRESS_REGEX = re.compile(r"^(.*?)(\s[0-9][0-9\S]*)?(?: - (.+))?$", flags=re.DOTALL)


# pylint: disable=C8107
class ResPartnerBank(models.Model):
    """This class upgrade the partners.bank to match Compassion needs."""

    _inherit = "res.partner.bank"

    def _l10n_ch_get_qr_vals(
        self,
        amount,
        currency,
        debtor_partner,
        free_communication,
        structured_communication,
    ):
        """
        Backport v18
        Returns a list of values for a Swiss QR bill.
        Allows invoices with no amount to let the payer choose the amount to pay.
        """
        filter_text = self._l10n_ch_filter_text
        comment = ""
        if free_communication:
            free_communication = filter_text(free_communication)
            comment = (
                (free_communication[:137] + "...")
                if len(free_communication) > 140
                else free_communication
            )

        (
            cred_street,
            cred_street_number,
            cred_zip,
            cred_city,
        ) = self._get_partner_address_lines(self.partner_id)
        (
            debt_street,
            debt_street_number,
            debt_zip,
            debt_city,
        ) = self._get_partner_address_lines(debtor_partner)

        # Compute reference type (empty by default, only mandatory for QR-IBAN,
        # and must then be 27 characters-long, with mod10r check digit as the 27th one)
        reference_type = "NON"
        reference = ""
        acc_number = self.sanitized_acc_number

        if self.l10n_ch_qr_iban:
            # ensures we can't have a QR-IBAN without a QR-reference here
            reference_type = "QRR"
            reference = structured_communication
            acc_number = sanitize_account_number(self.l10n_ch_qr_iban)
        elif self._is_iso11649_reference(structured_communication):
            reference_type = "SCOR"
            reference = structured_communication.replace(" ", "")

        currency = currency or self.currency_id or self.company_id.currency_id
        cred_name = filter_text(self.acc_holder_name or self.partner_id.name)
        debt_name = filter_text(debtor_partner.commercial_partner_id.name)

        result = [
            "SPC",  # QR Type
            "0200",  # Version
            "1",  # Coding Type
            acc_number,  # IBAN / QR-IBAN
            "S",  # Creditor Address Type
            cred_name[:70],  # Creditor Name
            cred_street,  # Creditor Street Name
            cred_street_number,  # Creditor Building Number
            cred_zip,  # Creditor Postal Code
            cred_city,  # Creditor Town
            self.partner_id.country_id.code,  # Creditor Country
            "",  # Ultimate Creditor Address Type
            "",  # Name
            "",  # Ultimate Creditor Address Line 1
            "",  # Ultimate Creditor Address Line 2
            "",  # Ultimate Creditor Postal Code
            "",  # Ultimate Creditor Town
            "",  # Ultimate Creditor Country
            "{:.2f}".format(amount) if amount else "",  # Amount
            currency.name,  # Currency
            "S",  # Ultimate Debtor Address Type
            debt_name[:70],  # Ultimate Debtor Name
            debt_street,  # Ultimate Debtor Street Name
            debt_street_number,  # Ultimate Debtor Building Number
            debt_zip,  # Ultimate Debtor Postal Code
            debt_city,  # Ultimate Debtor Town
            debtor_partner.country_id.code,  # Ultimate Debtor Country
            reference_type,  # Reference Type
            reference,  # Reference
            comment,  # Unstructured Message
            "EPD",  # Mandatory trailer part
        ]

        # newlines shift field content to a different line,
        # causing the QR code to be rejected
        return [
            (line or "").replace("\n", " ").encode("latin1", "replace").decode("latin1")
            for line in result
        ]

    def _l10n_ch_filter_text(self, value):
        value = " ".join((value or "").split())
        if value.isprintable() and value.isascii() or {*value} < UNICODE_ALLOWED:
            return value  # shortcut for performance
        forbidden = {*value} - UNICODE_ALLOWED
        for char in forbidden:
            value = value.replace(char, "")
        return value.strip()

    def _street_split(self, street):
        match = ADDRESS_REGEX.match(street or "")
        results = match.groups("") if match else ("", "", "")
        return {
            "street_name": results[0].strip(),
            "street_number": results[1].strip(),
            "street_number2": results[2],
        }

    def _get_partner_address_lines(self, partner):
        """Backport v18 for structured address in QR-bills
        :returns: tuple(street, street_number, zip, city)
        """
        filter_text = self._l10n_ch_filter_text
        street_split = self._street_split
        street_1_split = street_split(filter_text(partner.street))
        street_name = street_1_split["street_name"]
        building_number = (
            f"{street_1_split['street_number']} " f"{street_1_split['street_number2']}"
        ).strip()

        if building_number:
            concatenated_building_number = (
                f"{building_number} {filter_text(partner.street2)}".strip()
            )
            if len(concatenated_building_number) <= 16:
                building_number = concatenated_building_number
        else:
            # Try to complete the address with street2
            street_2_split = street_split(filter_text(partner.street2))

            building_number = (
                f"{street_2_split['street_number']} "
                f"{street_2_split['street_number2']}"
            ).strip()
            if building_number:
                street_name = f"{street_name} {street_2_split['street_name']}".strip()
            else:
                building_number = filter_text(partner.street2)

        return street_name[:70], building_number[:16], (partner.zip or "")[:16], (
            partner.city or ""
        )[:35]

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
