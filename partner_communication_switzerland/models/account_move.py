##############################################################################
#
#    Copyright (C) 2016-2023 Compassion CH (http://www.compassion.ch)
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

logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = "account.move"

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
                ("move_type", "=", "out_invoice"),
                ("invoice_category", "!=", "sponsorship"),
                ("payment_state", "=", "paid"),
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

    def _filter_invoice_to_thank(self):
        """
        Given a recordset of paid invoices, return only those that have
        to be thanked.
        :return: account.invoice recordset
        override thankyou_letters._filter_invoice_to_thanks()
        """
        return self.filtered(
            lambda i: i.move_type == "out_invoice"
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
                    and not any(
                        [
                            "Automatic" in name
                            for name in i.mapped("invoice_line_ids.name")
                        ]
                    )
                    and not self.env["recurring.contract.line"].search_count(
                        [
                            ("contract_id.type", "=", "G"),
                            ("contract_id.state", "=", "active"),
                            (
                                "sponsorship_id",
                                "in",
                                i.invoice_line_ids.mapped("contract_id").ids,
                            ),
                        ]
                    )
                )
            )
        )
