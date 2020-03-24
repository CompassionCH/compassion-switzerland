##############################################################################
#
#    Copyright (C) 2014-2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging
from datetime import datetime

from odoo import api, models, _
from odoo.addons.sponsorship_compassion.models.product_names import (
    GIFT_CATEGORY,
    SPONSORSHIP_CATEGORY,
)
from odoo.exceptions import UserError
from odoo.tools import float_round

logger = logging.getLogger(__name__)


class BankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def write(self, vals):
        """
        Override write method to link partner to bank when a statement line
        is added or updated
        """
        if "partner_id" in vals:
            for line in self.filtered("partner_account"):
                partner_bank = self.env["res.partner.bank"].search(
                    [
                        ("partner_id", "=", 1),
                        "|",
                        ("acc_number", "like", line.partner_account),
                        ("sanitized_acc_number", "like", line.partner_account),
                    ]
                )
                partner_bank.write({"partner_id": vals["partner_id"]})
        return super().write(vals)

    @api.multi
    def reconciliation_widget_auto_reconcile(self, num_already_reconciled):
        """
        Commit at each successful reconciliation.
        """
        num_reconciled = 0
        unreconciled_ids = list()
        notifications = list()
        for line in self:
            try:
                with self.env.cr.savepoint():
                    res = super(
                        BankStatementLine, line
                    ).reconciliation_widget_auto_reconcile(0)
                    num_reconciled += res["num_already_reconciled_lines"]
                    unreconciled_ids.extend(res["st_lines_ids"])
                    notifications.extend(res["notifications"])
            except:
                logger.error("Error when reconciling a statement line.")
        return {
            "st_lines_ids": unreconciled_ids,
            "notifications": notifications,
            "statement_name": False,
            "num_already_reconciled_lines": num_reconciled + num_already_reconciled,
        }

    @api.multi
    def auto_reconcile(self):
        """
        Extend automatic reconcile to allow one invoice selection when
        multiple invoices are matching.
        :return: account.move.line recordset of counterparts
        """
        self.ensure_one()
        res = super().auto_reconcile()
        if not res:
            # Code copied from base account_bank_statement : L669
            amount = self.amount_currency or self.amount
            company_currency = self.journal_id.company_id.currency_id
            st_line_currency = self.currency_id or self.journal_id.currency_id
            precision = (
                st_line_currency
                and st_line_currency.decimal_places
                or company_currency.decimal_places
            )
            params = {
                "company_id": self.env.user.company_id.id,
                "account_payable_receivable": (
                    self.journal_id.default_credit_account_id.id,
                    self.journal_id.default_debit_account_id.id,
                ),
                "amount": float_round(amount, precision_digits=precision),
                "partner_id": self.partner_id.id,
                "ref": self.ref,
            }
            currency = (
                (st_line_currency and st_line_currency != company_currency)
                and st_line_currency.id
                or False
            )
            sql_query = self._get_common_sql_query()
            sql_query += " AND aml.ref = %(ref)s AND ("
            sql_query += currency and "amount_residual_currency" or "amount_residual"
            sql_query += " = %(amount)s OR (acc.internal_type = 'liquidity'" " AND "
            sql_query += (
                currency and "amount_currency" or amount > 0 and "debit" or "credit"
            )
            sql_query += " = %(amount)s)) ORDER BY date_maturity asc," "aml.id asc"
            self.env.cr.execute(sql_query, params)
            match_recs = self.env.cr.dictfetchall()
            if len(match_recs) == 1:
                return self._reconcile(
                    self.env["account.move.line"].browse(
                        [aml.get("id") for aml in match_recs]
                    )
                )
            elif len(match_recs) > 1:
                # Take the first (current month or oldest one)
                match_recs = self.env["account.move.line"].browse(
                    [aml.get("id") for aml in match_recs]
                )
                res_sorted = list()
                today = datetime.today().date()
                for mv_line in match_recs:
                    mv_date = mv_line.date_maturity or mv_line.date

                    if mv_date.month == today.month and mv_date.year == today.year:
                        res_sorted.insert(0, mv_line.id)
                    else:
                        res_sorted.append(mv_line.id)
                res = match_recs.browse(res_sorted[0])
                return self._reconcile(res)
        return res

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _get_invoice_data(self, ref, mv_line_dicts):
        """ Add BVR payment mode in invoice. """
        inv_vals = super()._get_invoice_data(ref, mv_line_dicts)
        inv_vals["payment_mode_id"] = self.statement_id.journal_id.payment_mode_id.id
        return inv_vals

    def _get_invoice_line_data(self, mv_line_dict, invoice):
        invl_vals = super()._get_invoice_line_data(mv_line_dict, invoice)

        # Find sponsorship
        sponsorship_id = mv_line_dict.get("sponsorship_id")
        if not sponsorship_id:
            related_contracts = invoice.mapped("invoice_line_ids.contract_id")
            if related_contracts:
                sponsorship_id = related_contracts[0].id
        contract = self.env["recurring.contract"].browse(sponsorship_id)
        invl_vals["contract_id"] = contract.id

        # Force sponsorship when GIFT invoice is selected
        product = self.env["product.product"].browse(mv_line_dict["product_id"])
        if product.categ_name in (GIFT_CATEGORY, SPONSORSHIP_CATEGORY) and not contract:
            raise UserError(_("Add a Sponsorship"))

        # Find analytic default if possible
        default_analytic = self.env["account.analytic.default"].account_get(
            product.id, self.partner_id.id
        )
        analytic = invl_vals.get("account_analytic_id")
        if not analytic and default_analytic:
            invl_vals["account_analytic_id"] = default_analytic.id

        return invl_vals
