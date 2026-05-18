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
