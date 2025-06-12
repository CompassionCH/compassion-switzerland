from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _filter_direct_debit(self):
        """
        Exclude Direct Debit Order invoices,
        to avoid cancelling invoices that are being paid.
        Called by contracts when cancelling invoices.
        :return: account.move.line recordset, account.payment.order recordset
        """
        modified_orders = self.env["account.payment.order"]
        invoice_lines = self
        for move_line in self:
            payment_line = (
                self.env["account.payment.line"]
                .sudo()
                .search(
                    [
                        ("move_line_id.move_id", "=", move_line.move_id.id),
                        ("amount_currency", ">=", -move_line.amount_currency),
                        ("state", "!=", "cancel"),
                    ],
                    order="amount_currency ASC",
                    limit=1,
                )
            )
            if payment_line.state == "draft":
                # As the order is not yet validated, we can simply cancel the payment
                modified_orders |= payment_line.order_id
                if abs(payment_line.amount_currency) > abs(move_line.amount_currency):
                    payment_line.amount_currency -= abs(move_line.amount_currency)
                else:
                    payment_line.unlink()
            elif payment_line:
                # Remove all invoice lines because the invoice is being paid
                invoice_lines = invoice_lines.filtered(
                    lambda ivl, mvl=move_line: ivl.move_id != mvl.move_id
                )
        return invoice_lines, modified_orders
