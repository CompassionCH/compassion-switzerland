##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from datetime import datetime

from babel.dates import format_date

from odoo import api, models, fields, _
from odoo.exceptions import UserError

logger = logging.getLogger(__name__)

COMPASSION_QRR = "CH2430808007681434347"


class ContractGroup(models.Model):
    _inherit = ["recurring.contract.group", "translatable.model"]
    _name = "recurring.contract.group"

    @api.multi
    def get_months(self, months, sponsorships):
        """
        Given the list of months to print,
        returns the list of months grouped by the frequency payment
        of the contract group and only containing unpaid sponsorships.
        :param months: list of dates (date, datetime or string)
        :param sponsorships: recordset of included sponsorships
        :return: list of dates grouped in string format
        """
        self.ensure_one()
        freq = self.advance_billing_months
        payment_mode = self.with_context(lang="en_US").payment_mode_id
        # Take first open invoice or next_invoice_date
        open_invoice = min([i for i in sponsorships.mapped("first_open_invoice") if i])
        if open_invoice:
            first_invoice_date = open_invoice.replace(day=1)
        else:
            raise UserError(_("No open invoice found !"))

        for i, month in enumerate(months):
            if isinstance(month, str):
                months[i] = fields.Date.from_string(month)
            if isinstance(month, datetime):
                months[i] = month.date()

        # check if first invoice is after last month
        if first_invoice_date > months[-1]:
            raise UserError(_(f"First invoice is after Date Stop"))

        # Only keep unpaid months
        valid_months = [
            fields.Date.to_string(month) for month in months
            if month >= first_invoice_date
        ]
        if "Permanent" in payment_mode.name:
            return valid_months[:1]
        if freq == 1:
            return valid_months
        else:
            # Group months
            result = list()
            count = 1
            month_start = ""
            for month in valid_months:
                if not month_start:
                    month_start = month
                if count < freq:
                    count += 1
                else:
                    result.append(month_start + " - " + month)
                    month_start = ""
                    count = 1
            if not result:
                result.append(month_start + " - " + month)
            return result

    @api.multi
    def get_communication(self, start, stop, sponsorships):
        """
        Get the communication to print on the payment slip for sponsorship
        :param start: the month start for which we print the payment slip (string)
        :param stop: the month stop for which we print the payment slip (string)
        :param sponsorships: recordset of sponsorships for which to print the
                             payment slips
        :return: string of the communication
        """
        self.ensure_one()
        payment_mode = self.with_context(lang="en_US").payment_mode_id
        amount = self.get_amount(start, stop, sponsorships)
        valid = sponsorships
        number_sponsorship = len(sponsorships)
        date_start = fields.Date.to_date(start)
        date_stop = fields.Date.to_date(stop)
        vals = {
            "amount": f"CHF {amount:.0f}",
            "subject": _("for") + " ",
            "date": "",
        }
        locale = self.partner_id.lang
        context = {"lang": locale}
        if start and stop:
            start_date = format_date(date_start, format="MMMM yyyy", locale=locale)
            stop_date = format_date(date_stop, format="MMMM yyyy", locale=locale)
            if start == stop:
                vals["date"] = start_date
            else:
                vals["date"] = f"{start_date} - {stop_date}"
        if "Permanent" in payment_mode.name:
            vals["payment_type"] = _("ISR for standing order")
            vals["date"] = ""
        else:
            vals["payment_type"] = (
                _("ISR") + " " + self.contract_ids[0].with_context(
                    context).group_freq
            )
        if number_sponsorship > 1:
            vals["subject"] += str(number_sponsorship) + " " + _("sponsorships")
        elif number_sponsorship and valid.child_id:
            vals["subject"] = valid.child_id.preferred_name + " ({})".format(
                valid.child_id.local_id
            )
        elif number_sponsorship and not valid.child_id and valid.display_name:
            product_name = self.env["product.product"].search(
                [("id", "in", valid.mapped("contract_line_ids.product_id").ids)]
            )

            vals["subject"] = ", ".join(product_name.mapped("thanks_name"))

        return (
            f"{vals['payment_type']} {vals['amount']}"
            f"<br/>{vals['subject']}<br/>{vals['date']}"
        )

    @api.model
    def get_company_qrr_account(self):
        """ Utility to find the bvr account of the company. """
        return self.env["res.partner.bank"].search([
            ('acc_number', '=', COMPASSION_QRR)])

    def get_amount(self, start, stop, sponsorships):
        self.ensure_one()
        amount = sum(sponsorships.mapped("total_amount"))
        months = int(stop.split("-")[1]) - int(start.split("-")[1]) + 1
        payment_mode = self.with_context(lang="en_US").payment_mode_id
        if "Permanent" in payment_mode.name:
            months = self.advance_billing_months
        return amount * months
