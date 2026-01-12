import logging

from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model
    def _cron_charge_due_recurring_invoices(self):
        """
        CRON METHOD: Finds due invoices and triggers auto-payment.
        Should be scheduled to run daily (e.g., at 07:00 AM).
        """
        today = fields.Date.context_today(self)
        _logger.info(f"Starting Auto-Charge Cron for Due Date: {today}")

        # 1. Search for candidates
        # - Posted & Unpaid
        # - Due Date is Today (or in the past if missed)
        # - Linked to Recurring Engine
        invoices = self.search([
            ('state', '=', 'posted'),
            ('payment_state', '=', 'not_paid'),
            ('invoice_date_due', '=', today),  # Catch today's and any failed ones from before
            ('recurring_invoicer_id', '!=', False),
        ])

        _logger.info(f"Found {len(invoices)} invoices due for auto-charge check.")

        for invoice in invoices:
            try:
                invoice._process_auto_charge_if_eligible()
            except Exception as e:
                _logger.exception(f"Failed to auto-charge invoice {invoice.name}")
                # We catch exception to ensure one failure doesn't stop the whole cron
                continue

    def _process_auto_charge_if_eligible(self):
        """
        Separated logic to check eligibility and charge a specific invoice.
        """
        self.ensure_one()

        # 1. Find the related contract group
        contract_lines = self.invoice_line_ids.mapped("contract_id")
        if not contract_lines:
            return

        # All lines in one invoice belong to the same group
        group = contract_lines[0].group_id

        # 2. Payment Mode Validation
        if self.payment_mode_id and group.payment_mode_id:
            if self.payment_mode_id.id != group.payment_mode_id.id:
                return

        # 3. Check Token Existence
        if not (group.payment_token_id and group.payment_token_id.active):
            return

        # 4. Check for existing transactions (Avoid Double Charge)
        if self.transaction_ids.filtered(lambda t: t.state in ["done", "authorized", "pending"]):
            return

        # 5. EXECUTE CHARGE
        _logger.info(f"Auto-charging Invoice {self.name} (Due: {self.invoice_date_due})")

        # Use queue_job here if installed to parallelize the actual API calls
        if hasattr(self, 'with_delay'):
            self.with_delay(priority=10)._charge_postfinance_token(group.payment_token_id)
        else:
            self._charge_postfinance_token(group.payment_token_id)


    def _charge_postfinance_token(self, token):
        """
        Executes the S2S (Server to Server) transaction.
        """
        self.ensure_one()
        acquirer = token.acquirer_id

        timestamp = fields.Datetime.now().strftime("%Y%m%d%H%M%S")
        unique_reference = f"{self.name}-{timestamp}"

        # 1. Create Transaction (Draft)
        # [MIG] 18.0: TODO: use _postfinance_create_transaction from payment_postfinance_flex
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
                tx.write(
                    {"acquirer_reference": res.get("transaction_id"), "is_processed": True}
                )
                tx._set_transaction_done()
                tx._post_process_after_done()

            else:
                # Handle Failure
                error_msg = res.get("error", "Unknown Error")
                tx._set_transaction_error(msg=error_msg)
                self.message_post(body=f"Auto-payment failed via PostFinance: {error_msg}")
