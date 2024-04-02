##############################################################################
#
#    Copyright (C) 2014-2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import mod10r


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
            inv_vals["reference"] = vals["bvr_reference"]
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

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _build_invoice_gen_data(self, invoicing_date, invoicer, gift_wizard=False):
        """Inherit to add BVR ref and mandate"""
        inv_data = super()._build_invoice_gen_data(
            invoicing_date, invoicer, gift_wizard
        )
        bank_modes = (
            self.env["account.payment.mode"]
            .with_context(lang="en_US")
            .search([("payment_method_id.code", "=", "sepa.ch.dd")])
        )
        bank = self.payment_mode_id.fixed_journal_id.bank_account_id
        if gift_wizard:
            payment_reference = gift_wizard.contract_id.get_gift_bvr_reference(gift_wizard.product_id)
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
                "payment_reference": payment_reference,
                "mandate_id": mandate.id,
                "partner_bank_id": bank.id,
                "ref": self._prepare_ref_with_lang(invoicing_date)
            }
        )

        return inv_data

    def _prepare_ref_with_lang(self, invoicing_date):
        context = {"lang": self.partner_id.lang}
        communication = False
        active_contract = self.contract_ids.filtered(lambda l: l.state not in ("terminated","cancelled"))
        products = active_contract.contract_line_ids.product_id
        if len(active_contract.child_id) > 0:
            children = active_contract.mapped("child_id")
            if len(children) == 1:
                if len(products) == 1:
                    communication = products.name + " " + _("for")
                else:
                    communication = _("Sponsorship")
                    # communication = _("sponsorship gifts").title() + " " + _("for")
                communication += " " + children.preferred_name
            else:
                communication = str(len(children)) + " "
                communication += _("sponsorships")
                # communication += _("sponsorship gifts")
        elif len(products) == 1:
            communication = products.name
        communication += " " + _("Period: ") + invoicing_date.strftime("%B")

        return communication or ""
