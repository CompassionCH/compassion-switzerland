import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        """
        Extend action_post to trigger auto-payment if the invoice
        comes from a Recurring Contract with a Token.
        """
        # 1. Standard Post Logic
        res = super().action_post()

        # 2. Check for Auto-Pay candidates
        for invoice in self:
            # Only process Customer Invoices that are unpaid and from the Recurring engine
            if (
                invoice.move_type != "out_invoice"
                or invoice.payment_state != "not_paid"
                or not getattr(invoice, "recurring_invoicer_id", False)
            ):
                continue

            # Find the related contract group via invoice lines
            contract_lines = invoice.invoice_line_ids.mapped("contract_id")
            if not contract_lines:
                continue

            # All lines in one invoice belong to the same group
            group = contract_lines[0].group_id

            # If the invoice was generated with a different payment mode (e.g. BVR)
            # than the current group's mode (e.g. PostFinance Card), do not charge it.
            if invoice.payment_mode_id and group.payment_mode_id:
                if invoice.payment_mode_id.id != group.payment_mode_id.id:
                    _logger.info(
                        f"Skipping auto-charge for {invoice.name}: Invoice Mode ({invoice.payment_mode_id.name}) != Group Mode ({group.payment_mode_id.name})"
                    )
                    continue

            # 3. Trigger Charge if Token exists
            if group.payment_token_id and group.payment_token_id.active:
                # Double check: Do not charge if there is already a successful/pending transaction
                if invoice.transaction_ids.filtered(
                    lambda t: t.state in ["done", "authorized", "pending"]
                ):
                    _logger.info(
                        f"Skipping auto-charge for {invoice.name}: Valid transaction already exists."
                    )
                    continue

                _logger.info(
                    f"Auto-charging Invoice {invoice.name} with Token {group.payment_token_id.id}"
                )
                invoice._charge_postfinance_token(group.payment_token_id)

        return res


def _charge_postfinance_token(self, token):
    """
    Executes the S2S (Server to Server) transaction.
    """
    self.ensure_one()
    acquirer = token.acquirer_id

    timestamp = fields.Datetime.now().strftime("%Y%m%d%H%M%S")
    unique_reference = f"{self.name}-{timestamp}"

    # 1. Create Transaction (Draft)
    tx_vals = {
        "acquirer_id": acquirer.id,
        "amount": self.amount_total,
        "currency_id": self.currency_id.id,
        "partner_id": self.partner_id.id,
        "reference": unique_reference,
        "payment_token_id": token.id,
        "type": "server2server",
        "state": "draft",
        "invoice_ids": [(6, 0, self.ids)],
        "callback_model_id": self.env["ir.model"]._get_id("account.move"),
        "callback_res_id": self.id,
    }

    tx = self.env["payment.transaction"].create(tx_vals)

    # 2. Execute PostFinance Charge
    if acquirer.provider == "postfinance":
        res = acquirer.postfinance_charge_token(
            token, self.amount_total, self.currency_id, tx.reference, self.partner_id
        )

        if res.get("success"):
            # Update Transaction State
            tx._set_transaction_done()
            tx.write(
                {"acquirer_reference": res.get("transaction_id"), "is_processed": True}
            )

            tx._post_process_after_done()

        else:
            # Handle Failure
            error_msg = res.get("error", "Unknown Error")
            tx._set_transaction_error(msg=error_msg)
            self.message_post(body=f"Auto-payment failed via PostFinance: {error_msg}")
