##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
import re

from odoo import Command, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class BankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    def _get_fund_product(self):
        """Fund donation QRR reference, built as 9 digits + partner ref (7) +
        5 zeros + fund donation type (6) + fund id (4) + check digit
        (see res.partner.generate_bvr_reference). The bank puts it in the
        label, or in the move ref when the donor wrote a message.
        :return: the fund product.product, or empty recordset
        """
        product_obj = self.env["product.product"]
        for ref in (self.ref, self.payment_ref):
            match = re.fullmatch(r"\d{21}[67](\d{4})\d", (ref or "").strip())
            if match and int(match.group(1)):
                return product_obj.search(
                    [("fund_id", "=", int(match.group(1)))], limit=1
                )
        return product_obj

    def _get_fund_reconcile_model(self, product):
        """Use the write-off button of the fund if there is one, otherwise
        build a temporary model booking everything on the product's income
        account."""
        model_obj = self.env["account.reconcile.model"]
        reconcile_model = model_obj.search(
            [
                ("rule_type", "=", "writeoff_button"),
                ("company_id", "=", self.company_id.id),
                ("line_ids.product_id", "=", product.id),
            ],
            limit=1,
        )
        if reconcile_model:
            return reconcile_model
        account = product.with_company(self.company_id).property_account_income_id
        if not account:
            return model_obj
        analytic_distribution = self.env[
            "account.analytic.distribution.model"
        ]._get_distribution(
            {
                "product_id": product.id,
                "product_categ_id": product.categ_id.id,
                "partner_id": self.partner_id.id,
                "partner_category_id": self.partner_id.category_id.ids,
                "account_prefix": account.code,
                "company_id": self.company_id.id,
            }
        )
        return model_obj.new(
            {
                "name": product.name,
                "rule_type": "writeoff_button",
                "company_id": self.company_id.id,
                "line_ids": [
                    Command.create(
                        {
                            "account_id": account.id,
                            "product_id": product.id,
                            "label": product.name,
                            "analytic_distribution": analytic_distribution,
                        }
                    )
                ],
            }
        )

    def _do_auto_reconcile(self, models):
        """Fund donations are no longer invoiced. Recognize them from the QRR
        reference and book them with the write-off button of the fund product,
        which sets the account and the product used for the thank you letter.
        """
        self.ensure_one()
        if self.is_reconciled or not self._retrieve_partner():
            return super()._do_auto_reconcile(models)
        product = self._get_fund_product()
        reconcile_model = product and self._get_fund_reconcile_model(product)
        if not reconcile_model:
            return super()._do_auto_reconcile(models)
        try:
            with self.env.cr.savepoint():
                return self._reconcile_with_model(reconcile_model)
        except UserError as error:
            _logger.warning(
                "Fund auto reconcile skipped for statement line %s: %s",
                self.id,
                error,
            )
            return False

    def _reconcile_with_model(self, reconcile_model):
        liquidity_lines = self._seek_for_lines()[0]
        data = []
        for line in liquidity_lines:
            _, lines = self._get_reconcile_line(line, "liquidity", move=True)
            data += lines
        data, auxiliary_id = self._reconcile_data_by_model(data, reconcile_model, 1)
        if not reconcile_model.id:
            # Temporary model, it can't be referenced on the journal items
            for line in data:
                if line["kind"] == "other":
                    line["reconcile_model_id"] = False
        data = self._recompute_suspense_line(data, auxiliary_id, self.manual_reference)
        if not data.get("can_reconcile"):
            return False
        getattr(self, f"_reconcile_bank_line_{self.journal_id.reconcile_mode}")(
            self._prepare_reconcile_line_data(data["data"])
        )
        return True
