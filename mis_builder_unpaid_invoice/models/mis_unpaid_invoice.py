# Copyright 2018 Compassion Suisse
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
from os.path import join as opj

from odoo import api, fields, models, tools


class MisUnpaidInvoice(models.Model):

    _name = "mis.unpaid.invoice"
    _description = "MIS unpaid invoice"
    _auto = False

    line_type = fields.Char()
    name = fields.Char()
    account_id = fields.Many2one(comodel_name="account.account", string="Account",)
    invoice_id = fields.Many2one("account.invoice", string="Invoice",)
    journal_id = fields.Many2one("account.journal", string="Journal",)
    move_id = fields.Many2one("account.move", string="Accounting move",)
    analytic_account_id = fields.Many2one(
        "account.analytic.account", string="Analytic account",
    )
    product_id = fields.Many2one("product.product", string="Product",)
    company_id = fields.Many2one(comodel_name="res.company", string="Company",)
    credit = fields.Float()
    debit = fields.Float()
    date = fields.Date()

    @api.model_cr
    def init(self):
        script = opj(os.path.dirname(__file__), "mis_unpaid_invoice.sql")
        with open(script) as f:
            tools.drop_view_if_exists(self.env.cr, "mis_unpaid_invoice")
            self.env.cr.execute(f.read())
