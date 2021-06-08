##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, models
from odoo.addons.queue_job.job import job, related_action

logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.model
    def thankyou_summary_cron(self):
        """
        Sends a summary each month of the donations
        :return: True
        """
        comm_obj = self.env["partner.communication.job"]
        first = datetime.today().replace(day=1)
        last_month = first - relativedelta(months=1)
        partners = (
            self.env["res.users"]
                .search(
                [
                    "|",
                    "|",
                    ("name", "like", "Maglo Rachel"),
                    ("name", "like", "Willi Christian"),
                    ("name", "like", "Wulliamoz David"),
                ]
            )
            .mapped("partner_id")
        )
        invoices = self.search(
            [
                ("type", "=", "out_invoice"),
                ("invoice_category", "!=", "sponsorship"),
                ("state", "=", "paid"),
                ("last_payment", ">=", last_month),
                ("last_payment", "<", first),
            ]
        )
        config = self.env.ref("thankyou_letters.config_thankyou_summary")
        for partner in partners:
            comm_obj.create(
                {
                    "config_id": config.id,
                    "partner_id": partner.id,
                    "object_ids": invoices.ids,
                }
            )
        return True

    @api.multi
    def generate_thank_you(self):
        """
        Creates a thank you letter communication separating events thank you
        and regular thank you.
        override thankyou_letters.generate_thank_you()
        """
        partners = self.mapped("partner_id").filtered(
            lambda p: p.thankyou_preference != "none"
        )
        gift_category = self.env.ref("sponsorship_compassion.product_category_gift")
        for partner in partners:
            invoice_lines = self.mapped("invoice_line_ids").filtered(
                lambda l: l.partner_id == partner
            )
            event_thank = invoice_lines.filtered("event_id")
            other_thank = invoice_lines - event_thank
            for event in event_thank.mapped("event_id"):
                event_thank.filtered(lambda l: l.event_id == event).generate_thank_you()
            if other_thank:
                other_thank.generate_thank_you()

        # Send confirmation to ambassadors
        ambassadors = self.mapped("invoice_line_ids.user_id")
        for ambassador in ambassadors:
            # Filter only donations not for made for himself and filter
            # gifts that are thanked but not directly for ambassador.
            ambassador_lines = self.mapped("invoice_line_ids").filtered(
                lambda l: l.user_id == ambassador
                and l.partner_id != ambassador
                and l.product_id.categ_id != gift_category
            )
            if ambassador_lines:
                ambassador_lines.send_receipt_to_ambassador()

    @api.multi
    def _filter_invoice_to_thank(self):
        """
        Given a recordset of paid invoices, return only those that have
        to be thanked.
        :return: account.invoice recordset
        override thankyou_letters._filter_invoice_to_thanks()
        """
        return self.filtered(
            lambda i: i.type == "out_invoice"
            and not i.avoid_thankyou_letter
            and (
                  not i.communication_id
                  or i.communication_id.state in ("call", "pending")
            )
            and i.invoice_category != "sponsorship"
            and (
                  # Should not be thanked if it's linked to a contract
                  not i.mapped("invoice_line_ids.contract_id")
                  # But, can be thanked if it's a spontaneous gift
                  or (
                      i.invoice_category == "gift"
                      and i.origin != "Automatic birthday gift"
                      and not self.env["recurring.contract.line"].search_count([
                          ("contract_id.type", "=", "G"),
                          ("contract_id.state", "=", "active"),
                          ("sponsorship_id", "in",
                           i.invoice_line_ids.mapped("contract_id").ids)
                      ])
                  )
            )
        )

    @job(default_channel="root.group_reconcile")
    @related_action(action="related_action_invoices")
    def group_or_split_reconcile(self):
        """Reconcile given invoices with partner open payments.
        """
        super().group_or_split_reconcile()
        # Find if a communication with payment slips is pending and
        # regenerate it.
        jobs = self.env["partner.communication.job"].search(
            [
                ("model", "in", ["recurring.contract", "account.invoice"]),
                ("state", "!=", "done"),
                ("partner_id", "in", self.mapped("partner_id").ids),
            ]
        )
        jobs.refresh_text()
