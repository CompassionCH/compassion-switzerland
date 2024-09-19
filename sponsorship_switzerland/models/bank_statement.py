from odoo import api, models


class BankStatement(models.Model):
    _inherit = "account.bank.statement"

    @api.model_create_multi
    def create(self, values):
        # Associate generated invoices to bank statements
        res = super().create(values)
        for stmt in res:
            invoices = self.env["account.move"].search(
                [
                    ("bank_statement_id", "=", False),
                    ("invoice_origin", "=", stmt.name),
                ]
            )
            invoices.write({"bank_statement_id": stmt.id})
        return res
