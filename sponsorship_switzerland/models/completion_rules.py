##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging
import re

from odoo import fields, models
from odoo.tools.safe_eval import wrap_module

from odoo.addons.sponsorship_compassion.models.product_names import (
    GIFT_CATEGORY,
    GIFT_PRODUCTS_REF,
)

logger = logging.getLogger(__name__)


class StatementCompletionRule(models.Model):
    """Rules to complete account bank statements."""

    _inherit = "account.statement.completion.rule"

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################

    def _generate_invoice(self, stmts_vals, st_line, partner, ref_index):
        """
        Generates an invoice corresponding to the statement line read
        in order to reconcile the corresponding move lines.

        :param stmts_vals: bank statement values
        :param st_line: current statement line values
        :param partner: matched partner
        :param ref_index: starting index at which the partner ref was found
        :return: dict, boolean: st_line values to update, true if invoice is
                                created.
        """
        # Read data in english
        res = dict()
        ref = st_line["ref"]
        product = self.with_context(lang="en_US")._find_product_id(partner.ref, ref)
        if not product:
            return res, False
        # Don't generate invoice if it's a Sponsor gift
        if product.categ_name == GIFT_CATEGORY:
            res["name"] = product.name
            contract_obj = self.env["recurring.contract"].with_context(lang="en_US")
            # the contract number should be found after the ref on 5 digits.
            contract_index = ref_index + 7
            contract_number = int(ref[contract_index : contract_index + 5])
            search_criterias = [
                "|",
                ("partner_id", "=", partner.id),
                ("correspondent_id", "=", partner.id),
                ("state", "not in", ["terminated", "draft", "cancelled"]),
                ("type", "like", "S"),
            ]
            contract = contract_obj.search(
                search_criterias + [("commitment_number", "=", contract_number)]
            )
            if not contract:
                # Maybe the ref is misaligned. Most people have a number < 10
                # so we try to find this digit in the ref and see if we get
                # lucky.
                contract_number_match = re.search(partner.ref + r"0{1,4}(\d)", ref)
                if contract_number_match:
                    contract_number = int(contract_number_match.group(1))
                    contract = contract_obj.search(
                        search_criterias + [("commitment_number", "=", contract_number)]
                    )
            if len(contract) == 1:
                # Retrieve the birthday of child
                birthdate = ""
                if product.default_code == GIFT_PRODUCTS_REF[0]:
                    birthdate = contract.child_id.birthdate
                    birthdate = birthdate.strftime("%d %b")
                res["name"] += "[" + contract.child_code
                res["name"] += " (" + birthdate + ")]" if birthdate else "]"
            else:
                res["name"] += " [Child not found] "
            return res, False

        # Setup invoice data
        journal_id = (
            self.env["account.journal"].search([("type", "=", "sale")], limit=1).id
        )

        inv_data = {
            "account_id": partner.property_account_receivable_id.id,
            "move_type": "out_invoice",
            "partner_id": partner.id,
            "journal_id": journal_id,
            "invoice_date": st_line["date"],
            "payment_mode_id": self.env["account.payment.mode"]
            .search([("name", "=", "BVR")])
            .id,
            "ref": ref,
            "invoice_origin": stmts_vals["name"],
        }

        # Create invoice and generate invoice lines
        invoice = self.env["account.move"].with_context(lang="en_US").create(inv_data)
        res.update(
            self._generate_invoice_line(invoice.id, product, st_line, partner.id)
        )
        invoice.action_post()
        st_line.update(res)

    def _generate_invoice_line(self, invoice_id, product, st_line, partner_id):
        inv_line_data = {
            "name": st_line.get("note") or product.name,
            "account_id": product.property_account_income_id.id,
            "price_unit": st_line["amount"],
            "price_subtotal": st_line["amount"],
            "quantity": 1,
            "product_id": product.id or False,
            "move_id": invoice_id,
        }
        res = {}

        # Define analytic journal
        analytic = self.env["account.analytic.default"].account_get(
            product.id, partner_id, date=fields.Date.today()
        )
        if analytic.analytic_id:
            inv_line_data["analytic_account_id"] = analytic.analytic_id.id
        if analytic.analytic_tag_ids:
            inv_line_data["analytic_tag_ids"] = [(6, 0, analytic.analytic_tag_ids.ids)]

        res["name"] = product.name
        self.env["account.move.line"].create(inv_line_data)
        return res

    def _find_product_id(self, partner_ref, ref):
        """Finds what kind of payment it is,
        based on the reference of the statement line."""
        product_obj = self.env["product.product"].with_context(lang="en_US")
        # Search for payment type in a flexible manner given its neighbours
        # after partner ref: 5 digits for num pole,
        # 1 digit for type, 4 digit for code spe and 1 digit for cc
        payment_type_match = re.search(partner_ref + r"[0-9]{5}([0-9]){1}[0-9]{5}", ref)
        if payment_type_match:
            payment_type = int(payment_type_match.group(1))
            payment_type_index = payment_type_match.start(1)
        else:
            # Take payment type from its fixed position where it's supposed.
            payment_type_index = -6
            payment_type = int(ref[payment_type_index])
        product = 0
        if payment_type in range(1, 6):
            # Sponsor Gift
            products = product_obj.search(
                [("default_code", "=", GIFT_PRODUCTS_REF[payment_type - 1])]
            )
            product = products[0] if products else 0
        elif payment_type in range(6, 8):
            # Fund donation
            products = product_obj.search(
                [
                    (
                        "fund_id",
                        "=",
                        int(ref[payment_type_index + 1 : payment_type_index + 5]),
                    )
                ]
            )
            product = products[0] if products else 0

        return product

    def _get_base_dict(self, stmts_vals, stmt_line):
        eval_context = super()._get_base_dict(stmts_vals, stmt_line)
        eval_context.update(
            {
                "re": wrap_module(re, ["search"]),
                "generate_invoice": self._generate_invoice,
                "search_old_invoices": False,
            }
        )
        journal_codes = self.journal_ids.mapped("code")
        if "DD" in journal_codes or "LSV" in journal_codes:
            eval_context["search_old_invoices"] = True
        return eval_context
