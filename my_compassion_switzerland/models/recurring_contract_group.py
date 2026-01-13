from odoo import models


class RecurringContractGroup(models.Model):
    _inherit = "recurring.contract.group"

    def _process_invoice_generation(self, invoicer, invoice_date):
        """
        Override to ensure invoice_date_due is correctly computed
        immediately after creation.
        """
        # Allow the standard logic to create the invoice
        invoice = super()._process_invoice_generation(invoicer, invoice_date)

        # Ensure Payment Terms are set (Inherit from Partner if missing)
        if (
            not invoice.invoice_payment_term_id
            and invoice.partner_id.property_payment_term_id
        ):
            invoice.invoice_payment_term_id = (
                invoice.partner_id.property_payment_term_id
            )

        # Force Due Date Calculation
        # We manually trigger the logic that calculates 'invoice_date_due'
        if invoice.invoice_payment_term_id and invoice.invoice_date:
            invoice._onchange_invoice_date()
            invoice._onchange_invoice_payment_term_id()

        # Fallback: If still no due date (e.g., no terms set), use the Invoice Date (Immediate Payment)
        if not invoice.invoice_date_due:
            invoice.invoice_date_due = invoice.invoice_date

        return invoice
