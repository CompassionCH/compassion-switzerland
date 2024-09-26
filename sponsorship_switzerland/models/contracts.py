##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import mod10r

from odoo.addons.sponsorship_compassion.models.product_names import GIFT_PRODUCTS_REF

logger = logging.getLogger(__name__)


class RecurringContracts(models.Model):
    _inherit = "recurring.contract"

    first_open_invoice = fields.Date(compute="_compute_first_open_invoice")
    mandate_date = fields.Datetime()
    has_mandate = fields.Boolean(compute="_compute_has_mandate")
    church_id = fields.Many2one(related="partner_id.church_id", readonly=True)
    previous_child_id = fields.Many2one(
        "compassion.child",
        "Previous child",
        related="parent_id.child_id",
        readonly=False,
    )
    is_already_a_sponsor = fields.Boolean(
        compute="_compute_already_a_sponsor", store=True
    )
    next_waiting_reminder = fields.Datetime(
        "Next reminder", compute="_compute_next_reminder", store=True
    )
    hillsong_ref = fields.Char(related="origin_id.hillsong_ref", store=True)
    state = fields.Selection(
        selection_add=[("mandate", "Waiting Mandate")],
        ondelete={"mandate": lambda records: records.write({"state": "waiting"})},
    )

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    def _compute_first_open_invoice(self):
        for contract in self:
            invoices = contract.invoice_line_ids.mapped("move_id").filtered(
                lambda i: i.payment_state == "not_paid"
            )
            if invoices:
                first_open_invoice = min(i.invoice_date for i in invoices)
                contract.first_open_invoice = first_open_invoice
            elif contract.state not in ("terminated", "cancelled"):
                contract.first_open_invoice = contract.group_id.current_invoice_date
            else:
                contract.first_open_invoice = False

    def _compute_has_mandate(self):
        # Search for an existing valid mandate
        for contract in self:
            count = self.env["account.banking.mandate"].search_count(
                [("partner_id", "=", contract.partner_id.id), ("state", "=", "valid")]
            )
            if contract.partner_id.parent_id:
                count += self.env["account.banking.mandate"].search_count(
                    [
                        ("partner_id", "=", contract.partner_id.parent_id.id),
                        ("state", "=", "valid"),
                    ]
                )
            contract.has_mandate = bool(count)

    def _compute_already_a_sponsor(self):
        for contract in self:
            contract.is_already_a_sponsor = (
                True if contract.previous_child_id else False
            )

    @api.depends("child_id.hold_id.expiration_date")
    def _compute_next_reminder(self):
        for sponsorship in self:
            if sponsorship.child_id.hold_id:
                hold_expiration = sponsorship.child_id.hold_id.expiration_date
                sponsorship.next_waiting_reminder = fields.Datetime.to_string(
                    hold_expiration - relativedelta(days=7)
                )
            else:
                sponsorship.next_waiting_reminder = False

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    def write(self, vals):
        """Perform various checks when a contract is modified."""
        if "group_id" in vals:
            old_payment_modes = [g.payment_mode_id for g in self.mapped("group_id")]
        super().write(vals)
        if "group_id" in vals and old_payment_modes:
            self.check_mandate_needed(old_payment_modes)
        return True

    @api.onchange("child_id")
    def onchange_child_id(self):
        res = super().onchange_child_id()
        warn_categories = self.correspondent_id.category_id.filtered("warn_sponsorship")
        if warn_categories:
            cat_names = warn_categories.mapped("name")
            return {
                "warning": {
                    "title": _("The sponsor has special categories"),
                    "message": ", ".join(cat_names),
                }
            }
        return res

    @api.onchange("ambassador_id")
    def onchange_ambassador_id(self):
        """Make checks as well when ambassador is changed."""
        warn_categories = self.ambassador_id.category_id.filtered("warn_sponsorship")
        if warn_categories:
            cat_names = warn_categories.mapped("name")
            return {
                "warning": {
                    "title": _("The ambassador has special categories"),
                    "message": ", ".join(cat_names),
                }
            }

    def postpone_reminder(self):
        self.ensure_one()
        extension = self.child_id.hold_id.no_money_extension
        if extension > 2:
            extension = 2
        wizard = self.env["postpone.waiting.reminder.wizard"].create(
            {
                "sponsorship_id": self.id,
                "next_reminder": self.next_waiting_reminder,
                "next_reminder_type": str(extension),
            }
        )
        return {
            "name": _("Postpone reminder"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": wizard._name,
            "context": self.env.context,
            "res_id": wizard.id,
            "target": "new",
        }

    def get_gift_bvr_reference(self, product):
        product = product.with_context(lang="en_US")
        ref = self.gift_partner_id.ref
        bvr_reference = "0" * (9 + (7 - len(ref))) + ref
        commitment_number = str(self.commitment_number)
        bvr_reference += "0" * (5 - len(commitment_number)) + commitment_number
        # Type of gift
        bvr_reference += str(GIFT_PRODUCTS_REF.index(product.default_code) + 1)
        bvr_reference += "0" * 4

        if self.payment_mode_id and "LSV" in self.payment_mode_id.name:
            # Get company BVR adherent number
            user = self.env.user
            bank_obj = self.env["res.partner.bank"]
            company_bank = bank_obj.search(
                [
                    ("partner_id", "=", user.company_id.partner_id.id),
                    ("l10n_ch_isr_subscription_chf", "!=", False),
                    ("acc_type", "=", "iban"),
                ],
                limit=1,
            )
            if company_bank:
                bvr_reference = company_bank.l10n_ch_isrb_id_number + bvr_reference[9:]
        if len(bvr_reference) == 26:
            return mod10r(bvr_reference)

        return False

    ##########################################################################
    #                            WORKFLOW METHODS                            #
    ##########################################################################
    def contract_active(self):
        """Hook for doing something when contract is activated.
        Update partner to add the 'Sponsor' category
        """
        check_duplicate_activity_id = False
        check_duplicate_activity_id = self.env.ref(
            "partner_auto_match.activity_check_duplicates"
        ).id
        if self.mapped("partner_id.activity_ids").filtered(
            lambda act: act.activity_type_id.id == check_duplicate_activity_id
        ) or self.mapped("correspondent_id.activity_ids").filtered(
            lambda act: act.activity_type_id.id == check_duplicate_activity_id
        ):
            raise UserError(
                _("Please verify the partner before validating the " "sponsorship")
            )
        super().contract_active()
        sponsor_cat_id = self.env.ref(
            "partner_compassion.res_partner_category_sponsor"
        ).id
        old_sponsor_cat_id = self.env.ref(
            "partner_compassion.res_partner_category_old"
        ).id
        sponsorships = self.filtered(lambda c: "S" in c.type)
        add_sponsor_vals = {
            "category_id": [(4, sponsor_cat_id), (3, old_sponsor_cat_id)]
        }
        partners = sponsorships.mapped("partner_id") | sponsorships.mapped(
            "correspondent_id"
        )
        partners.write(add_sponsor_vals)
        return True

    def contract_waiting_mandate(self):
        need_mandate = self.filtered(lambda s: not s.partner_id.valid_mandate_id)
        if need_mandate:
            need_mandate.write(
                {"state": "mandate", "mandate_date": fields.Datetime.now()}
            )
        return True

    def contract_waiting(self):
        """If sponsor has open payments, generate invoices and reconcile."""
        self._check_sponsorship_is_valid()
        sponsorships = self.filtered(lambda s: "S" in s.type)
        needs_mandate = self.env[self._name]
        for contract in sponsorships:
            payment_mode = contract.payment_mode_id.name
            if (
                payment_mode is not False
                and contract.type in ["S", "SC", "SWP"]
                and ("LSV" in payment_mode or "Postfinance" in payment_mode)
                and contract.total_amount != 0
                and not contract.partner_id.valid_mandate_id
            ):
                # Check mandate
                needs_mandate += contract
        super().contract_waiting()
        if needs_mandate:
            needs_mandate.contract_waiting_mandate()
        return True

    def mandate_valid(self):
        # Called when mandate is validated
        to_transition = self.filtered(lambda c: c.state == "mandate")
        to_active = to_transition.filtered("is_active")
        to_active.contract_active()
        (to_transition - to_active).contract_waiting()
        return True

    def _check_sponsorship_is_valid(self):
        """
        Called at contract validation to ensure we can validate the
        sponsorship.
        """
        partners = self.mapped("partner_id") | self.mapped("correspondent_id")
        if partners.filtered("is_restricted"):
            raise UserError(
                _(
                    "This partner has the restricted category active. "
                    "New sponsorships are not allowed."
                )
            )
        # Notify for special categories
        special_categories = partners.mapped("category_id").filtered("warn_sponsorship")
        # Since we are in workflow, the user is not set in environment.
        # We take then the last write user on the records
        if special_categories:
            self.env.user.notify_warning(
                ", ".join(special_categories.mapped("name")),
                title=_("The sponsor has special categories"),
                sticky=True,
            )

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _on_sponsorship_finished(self):
        """Called when a sponsorship is terminated or cancelled:
        Remove sponsor category if sponsor has no other active
        sponsorships.
        """
        super()._on_sponsorship_finished()
        sponsor_cat_id = self.env.ref(
            "partner_compassion.res_partner_category_sponsor"
        ).id
        old_sponsor_cat_id = self.env.ref(
            "partner_compassion.res_partner_category_old"
        ).id

        for sponsorship in self:
            partner_id = sponsorship.partner_id.id
            correspondent_id = sponsorship.correspondent_id.id
            # Partner
            contract_count = self.search_count(
                [
                    "|",
                    ("correspondent_id", "=", partner_id),
                    ("partner_id", "=", partner_id),
                    ("state", "=", "active"),
                    ("type", "like", "S"),
                ]
            )
            if not contract_count:
                # Replace sponsor category by old sponsor category
                sponsorship.partner_id.write(
                    {"category_id": [(3, sponsor_cat_id), (4, old_sponsor_cat_id)]}
                )
            # Correspondent
            contract_count = self.search_count(
                [
                    "|",
                    ("correspondent_id", "=", correspondent_id),
                    ("partner_id", "=", correspondent_id),
                    ("state", "=", "active"),
                    ("type", "like", "S"),
                ]
            )
            if not contract_count:
                # Replace sponsor category by old sponsor category
                sponsorship.correspondent_id.write(
                    {"category_id": [(3, sponsor_cat_id), (4, old_sponsor_cat_id)]}
                )

    def check_mandate_needed(self, old_payment_modes):
        """Change state of contract if payment is changed to/from LSV or DD."""
        for i, contract in enumerate(self):
            group = contract.group_id.with_context(lang="en_US")
            payment_name = group.payment_mode_id.name
            old_payment_name = old_payment_modes[i].with_context(lang="en_US").name
            if not old_payment_name:
                continue
            if ("LSV" in payment_name or "Postfinance" in payment_name) and not (
                "LSV" in old_payment_name or "Postfinance" in old_payment_name
            ):
                self.filtered(
                    lambda s: s.state in ["waiting", "active"]
                ).contract_waiting_mandate()
            elif (
                "LSV" in old_payment_name or "Postfinance" in old_payment_name
            ) and not ("LSV" in payment_name or "Postfinance" in payment_name):
                contract.mandate_valid()
