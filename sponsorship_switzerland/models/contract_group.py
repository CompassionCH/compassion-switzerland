##############################################################################
#
#    Copyright (C) 2014-2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester, Emanuel Cino, Jérémie Lang
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import format_date, mod10r


class ContractGroup(models.Model):
    """Add BVR on groups and add BVR ref and analytic_id
    in invoices"""

    _inherit = "recurring.contract.group"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    bvr_reference = fields.Char("BVR Ref", tracking=True)

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.depends("payment_mode_id", "bvr_reference", "partner_id")
    def name_get(self):
        res = list()
        for gr in self:
            name = ""
            if gr.payment_mode_id:
                name = gr.payment_mode_id.name
            if gr.bvr_reference:
                name += " " + gr.bvr_reference
            if name == "":
                name = gr.partner_id.name + " " + str(gr.id)
            res.append((gr.id, name))
        return res

    def write(self, vals):
        """If sponsor changes his payment term to LSV or DD,
        change the state of related contracts so that we wait
        for a valid mandate before generating new invoices.
        """
        contracts = self.env["recurring.contract"]
        inv_vals = dict()
        if "payment_mode_id" in vals:
            inv_vals["payment_mode_id"] = vals["payment_mode_id"]
            payment_mode = (
                self.env["account.payment.mode"]
                .with_context(lang="en_US")
                .browse(vals["payment_mode_id"])
            )
            payment_name = payment_mode.name
            contracts |= self.mapped("contract_ids")
            for group in self:
                if "LSV" in payment_name or "Postfinance" in payment_name:
                    # LSV/DD Contracts need no reference
                    if group.bvr_reference and "multi-months" not in payment_name:
                        vals["bvr_reference"] = False
        if "bvr_reference" in vals:
            inv_vals["payment_reference"] = vals["bvr_reference"]
            contracts |= self.mapped("contract_ids")

        if contracts:
            # Update related open invoices to reflect the changes
            inv_lines = self.env["account.move.line"].search(
                [
                    ("contract_id", "in", contracts.ids),
                    ("payment_state", "=", "not_paid"),
                ]
            )
            invoices = inv_lines.mapped("move_id")
            invoices.button_draft()
            invoices.write(inv_vals)
            invoices.action_post()

        # When the payment mode changes to LSV or DD, we need to update the related open
        # invoices (block above) and raise any errors first before changing the status
        # of the contracts (block below). Otherwise if an error occurs, we have an
        # undesirable situation where the status of the contracts are modified and the
        # payment method did not successfully change.
        if "payment_mode_id" in vals:
            old_modes = []
            for group in self:
                old_mode = group.payment_mode_id.with_context(lang="en_US")
                old_modes.append([old_mode] * len(group.contract_ids))

        res = super().write(vals)

        if "payment_mode_id" in vals:
            for i, group in enumerate(self):
                group.contract_ids.check_mandate_needed(old_modes[i])

        return res

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def compute_partner_bvr_ref(self, partner=None, is_lsv=False):
        """Generates a new BVR Reference.
        See file /nas/it/devel/Code_ref_BVR.xls for more information."""
        self.ensure_one()
        if self.exists():
            # If group was already existing, retrieve any existing reference
            ref = self.bvr_reference
            if ref:
                return ref
        partner = partner or self.partner_id
        result = "0" * (9 + (7 - len(partner.ref))) + partner.ref
        count_groups = str(self.search_count([("partner_id", "=", partner.id)]))
        result += "0" * (5 - len(count_groups)) + count_groups
        # Type '0' = Sponsorship
        result += "0"
        result += "0" * 4

        if is_lsv:
            result = "004874969" + result[9:]
        if len(result) == 26:
            return mod10r(result)

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.onchange("partner_id")
    def on_change_partner_id(self):
        if not self.partner_id:
            self.bvr_reference = False
            return

        partner = self.partner_id
        if partner.ref:
            computed_ref = self.compute_partner_bvr_ref(partner)
            if computed_ref:
                self.bvr_reference = computed_ref
            else:
                raise UserError(
                    _(
                        "The reference of the partner has not been set, "
                        "or is in wrong format. Please make sure to enter a "
                        "valid BVR reference for the contract."
                    )
                )

    @api.onchange("payment_mode_id")
    def on_change_payment_mode(self):
        """Generate new bvr_reference if payment term is Permanent Order
        or BVR"""
        payment_mode_id = self.payment_mode_id.id
        pmobj = self.env["account.payment.mode"].with_context(lang="en_US")
        need_bvr_ref_term_ids = pmobj.search(
            [
                "|",
                ("name", "in", ("Permanent Order", "BVR")),
                ("name", "like", "multi-months"),
            ]
        ).ids
        lsv_term_ids = pmobj.search([("name", "like", "LSV")]).ids
        if payment_mode_id in need_bvr_ref_term_ids:
            is_lsv = payment_mode_id in lsv_term_ids
            partner = self.partner_id
            if partner.ref and (not self.bvr_reference or is_lsv):
                self.bvr_reference = self.compute_partner_bvr_ref(partner, is_lsv)
        else:
            self.bvr_reference = False

    @api.onchange("bvr_reference")
    def on_change_bvr_ref(self):
        """Test the validity of a reference number."""
        bvr_reference = self.bvr_reference
        is_valid = bvr_reference and bvr_reference.isdigit()
        if is_valid and len(bvr_reference) == 26:
            bvr_reference = mod10r(bvr_reference)
        elif is_valid and len(bvr_reference) == 27:
            valid_ref = mod10r(bvr_reference[:-1])
            is_valid = valid_ref == bvr_reference
        else:
            is_valid = False

        if is_valid:
            self.bvr_reference = bvr_reference
        elif bvr_reference:
            raise UserError(
                _(
                    "The reference of the partner has not been set, or is in "
                    "wrong format. Please make sure to enter a valid BVR "
                    "reference for the contract."
                )
            )

    def convert_date_to_client_month(self, date_obj, lang):
        """
        Convert the given date object to a month representation in the language
        specified by the customer.
        Args:
            date_obj (datetime.date): The date object to be converted.
            lang (str): The language code representing the language preferred
            by the customer.
        Returns:
            str: A string representing the month and year in the language specified
            by the customer.
        Note:
            This function relies on an external method 'format_date' to format the date
            object according to
            the specified language. Ensure that the 'format_date' method is available
            and correctly configured within your environment.
        """
        formatted_month = format_date(
            self.env, value=date_obj, date_format="MMMM YYYY", lang_code=lang
        )
        return formatted_month.capitalize()

    def get_unique_occurrence(self, data, key, multiple_result_expected=False):
        """
        Get unique occurrence(s) of a given key in the data dictionary.
        Args:
            data (dict or defaultdict): The dictionary containing the data.
            key (hashable): The key whose occurrence(s) need to be retrieved.
            multiple_result_expected (bool, optional): Flag indicating if multiple
            results are expected.
                If True, returns a comma-separated string of unique occurrences.
                If False (default), returns False
                when more than one unique occurrence is found.
        Returns:
            str or bool: The unique occurrence(s) of the key.
            If multiple_result_expected is False and there are
                more than one unique occurrences or the key doesn't exist,
                it returns False. If multiple_result_expected
                is True or there are multiple unique occurrences,
                it returns a comma-separated string. If there's only
                one unique occurrence, it returns a string.
        """
        if key not in data:
            occurrences = []
            for entry in data.values():
                occurrences.extend(entry[key])
        else:
            occurrences = data[key]

        unique_occurrences = list(set(occurrences))

        if len(unique_occurrences) == 1:
            return str(unique_occurrences[0])
        elif multiple_result_expected:
            return ", ".join(map(str, unique_occurrences))
        else:
            return False

    def is_less_than_twenty_percent_of_total(self, contract_id, line_amount):
        """
        Check if a given line amount is less than twenty percent of the total amount
        of contract lines.
        Args:
            contract_id (object): The contract object containing line items.
            line_amount (float): The amount of the line to be checked.
        Returns:
            bool: True if the line amount is less than twenty percent of the total
            contract amount,
                otherwise False.
        """
        contract = contract_id.contract_line_ids
        total_amount = 0
        for line in contract:
            total_amount += line.subtotal

        twenty_percent_of_total = total_amount * 20 / 100
        if line_amount < twenty_percent_of_total:
            return True

        return False

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _build_invoice_gen_data(
        self, invoicing_date, invoicer, contract, gift_wizard=False
    ):
        """Inherit to add BVR ref and mandate"""
        inv_data = super()._build_invoice_gen_data(
            invoicing_date, invoicer, contract, gift_wizard
        )
        ref = self.with_context(lang=self.partner_id.lang)._compute_ref(
            invoicing_date, gift_wizard
        )
        payment_reference = ""
        bank_modes = (
            self.env["account.payment.mode"]
            .with_context(lang="en_US")
            .search([("payment_method_id.code", "=", "sepa.ch.dd")])
        )
        bank = self.payment_mode_id.fixed_journal_id.bank_account_id
        if gift_wizard:
            payment_reference = gift_wizard.contract_id.get_gift_bvr_reference(
                gift_wizard.product_id
            )
        elif self.bvr_reference:
            payment_reference = self.bvr_reference
        elif self.payment_mode_id in bank_modes:
            seq = self.env["ir.sequence"]
            payment_reference = mod10r(seq.next_by_code("contract.bvr.ref"))
        mandate = self.env["account.banking.mandate"].search(
            [("partner_id", "=", self.partner_id.id), ("state", "=", "valid")], limit=1
        )
        inv_data.update(
            {
                "ref": ref,
                "mandate_id": mandate.id,
                "partner_bank_id": bank.id,
                "payment_reference": payment_reference,
            }
        )

        return inv_data

    def _compute_ref(self, invoicing_date, gift_wizard):
        """Compute a comprehensive reference for customer"""
        lang = self.partner_id.lang
        ref = ""
        contract_lines = self.active_contract_ids.contract_line_ids
        occurrences = defaultdict(
            lambda: {"count": 0, "name": "", "child": [], "period": []}
        )

        if gift_wizard:
            gift = gift_wizard.with_context(lang=lang)
            product_name = gift.product_id.name
            child_preferred_name = gift.contract_id.child_id.preferred_name

            if gift_wizard.description != gift_wizard.product_id.display_name:
                ref = (
                    f"{product_name} {_('for')}: {child_preferred_name}. "
                    f"{_('Additional comments')}: {gift.description} "
                )
            elif gift_wizard.description == gift_wizard.product_id.display_name:
                ref = f"{product_name} {_('for')}: {child_preferred_name} "

            return ref[:150]

        for line in contract_lines:
            product = line.product_id
            period = self.convert_date_to_client_month(invoicing_date, lang)
            child = line.contract_id.child_id
            child_preferred_name = child.preferred_name

            if not self.is_less_than_twenty_percent_of_total(
                line.contract_id, line.subtotal
            ):
                details = occurrences[product.id]
                details["count"] += 1
                details["name"] = (
                    product.plural_name if details["count"] > 1 else product.name
                )
                details["period"].append(period)
                if child:
                    details["child"].append(child_preferred_name)

        unique_period = self.get_unique_occurrence(dict(occurrences), "period", True)

        for details in occurrences.values():
            unique_children = self.get_unique_occurrence(details, "child")
            ref_parts = [f"{details['count']} {details['name']}"]

            if details["child"] and unique_children:
                ref_parts.append(f"{_('for')} {unique_children}")

            ref += " ".join(ref_parts) + ". "

        ref += f"{_('Period')}: {unique_period}."

        return ref[:150]
