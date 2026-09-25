##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _invoice_paid_hook(self):
        res = super()._invoice_paid_hook()
        invoices = self.filtered(lambda move: move.move_type == "out_invoice")
        if not invoices:
            return res
        self.env["event.registration.task.rel"].sudo().search(
            [
                ("done", "=", False),
                "|",
                "&",
                (
                    "task_id",
                    "=",
                    self.env.ref("website_switzerland.task_down_payment").id,
                ),
                ("registration_id.down_payment_id", "in", invoices.ids),
                "&",
                (
                    "task_id",
                    "=",
                    self.env.ref("website_switzerland.task_full_payment").id,
                ),
                ("registration_id.trip_invoice_id", "in", invoices.ids),
            ]
        ).write({"done": True})
        return res
