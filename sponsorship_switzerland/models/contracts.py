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
import datetime

from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError
from odoo.tools import mod10r
from odoo import api, models, fields, _

logger = logging.getLogger(__name__)


class RecurringContracts(models.Model):
    _inherit = "recurring.contract"

    first_open_invoice = fields.Date(compute="_compute_first_open_invoice")
    mandate_date = fields.Datetime(string="State last time mandate")
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
    partner_lang = fields.Selection(
        "res.partner", "Partner language", related="partner_id.lang", store=True
    )
    hillsong_ref = fields.Char(related="origin_id.hillsong_ref", store=True)
    state = fields.Selection(selection_add=[("mandate", "Waiting Mandate")])

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.multi
    def _compute_first_open_invoice(self):
        for contract in self:
            invoices = contract.invoice_line_ids.mapped("invoice_id").filtered(
                lambda i: i.state == "open"
            )
            if invoices:
                first_open_invoice = min([i.date_invoice for i in invoices])
                contract.first_open_invoice = first_open_invoice
            elif contract.state not in ("terminated", "cancelled"):
                contract.first_open_invoice = contract.next_invoice_date

    @api.multi
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

    @api.multi
    def _compute_already_a_sponsor(self):
        for contract in self:
            contract.is_already_a_sponsor = (
                True if contract.previous_child_id else False
            )

    @api.depends("child_id.hold_id.expiration_date")
    @api.multi
    def _compute_next_reminder(self):
        for sponsorship in self.filtered(lambda s: s.child_id.hold_id):
            hold_expiration = sponsorship.child_id.hold_id.expiration_date
            sponsorship.next_waiting_reminder = fields.Datetime.to_string(
                hold_expiration - relativedelta(days=7)
            )

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.multi
    def write(self, vals):
        """ Perform various checks when a contract is modified. """
        if "group_id" in vals:
            old_payment_modes = [g.payment_mode_id for g in self.mapped('group_id')]
        super().write(vals)
        if "group_id" in vals:
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

    @api.onchange("user_id")
    def onchange_user_id(self):
        """ Make checks as well when ambassador is changed. """
        warn_categories = self.user_id.category_id.filtered("warn_sponsorship")
        if warn_categories:
            cat_names = warn_categories.mapped("name")
            return {
                "warning": {
                    "title": _("The ambassador has special categories"),
                    "message": ", ".join(cat_names),
                }
            }

    @api.onchange("group_id")
    def on_change_group_id(self):
        """ Compute next invoice_date """
        current_date = datetime.date.today()
        is_active = False

        if self.state not in ("draft", "mandate") and self.next_invoice_date:
            is_active = True
            current_date = self.next_invoice_date

        if self.group_id:
            contract_group = self.group_id
            if contract_group.next_invoice_date:
                next_group_date = contract_group.next_invoice_date
                next_invoice_date = current_date.replace(day=next_group_date.day)
            else:
                next_invoice_date = current_date.replace(day=1)
            payment_mode = contract_group.payment_mode_id.name
        else:
            next_invoice_date = current_date.replace(day=1)
            payment_mode = ""

        if current_date.day > 15 or (
                payment_mode in ("LSV", "Postfinance") and not is_active
        ):
            next_invoice_date += relativedelta(months=+1)
        self.next_invoice_date = next_invoice_date

    @api.multi
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
            "view_type": "form",
            "view_mode": "form",
            "res_model": wizard._name,
            "context": self.env.context,
            "res_id": wizard.id,
            "target": "new",
        }

    ##########################################################################
    #                            WORKFLOW METHODS                            #
    ##########################################################################
    @api.multi
    def contract_active(self):
        """ Hook for doing something when contract is activated.
        Update partner to add the 'Sponsor' category
        """
        super().contract_active()
        if self.mapped("partner_id.activity_ids") or self.mapped("correspondent_id.activity_ids"):
            raise UserError(
                _("Please verify the partner before validating the sponsorship")
            )

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

    @api.multi
    def contract_waiting_mandate(self):
        need_mandate = self.filtered(lambda s: not s.partner_id.valid_mandate_id)
        need_mandate.write({"state": "mandate", "mandate_date": fields.Datetime.now()})
        return True

    @api.multi
    def contract_waiting(self):
        """ If sponsor has open payments, generate invoices and reconcile. """
        self._check_sponsorship_is_valid()
        sponsorships = self.filtered(lambda s: "S" in s.type)
        needs_mandate = self.env[self._name]
        for contract in sponsorships:
            payment_mode = contract.payment_mode_id.name
            if (
                    contract.type in ["S", "SC"]
                    and ("LSV" in payment_mode or "Postfinance" in payment_mode)
                    and contract.total_amount != 0
            ):
                # Check mandate
                needs_mandate += contract
                # Recompute next_invoice_date
                today = datetime.date.today()
                old_invoice_date = contract.next_invoice_date
                next_invoice_date = old_invoice_date.replace(
                    month=today.month, year=today.year
                )
                if today.day > 15 and next_invoice_date.day < 15:
                    next_invoice_date = next_invoice_date + relativedelta(months=+1)
                if next_invoice_date > old_invoice_date:
                    contract.next_invoice_date = next_invoice_date
            super(RecurringContracts, contract).contract_waiting()
            contract._reconcile_open_amount()

        needs_mandate.contract_waiting_mandate()
        super(RecurringContracts, self - sponsorships).contract_waiting()
        return True

    @api.multi
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
        if self.mapped("partner_id.activity_ids") or self.mapped("correspondent_id.activity_ids"):
            raise UserError(
                _("Please verify the partner before validating the sponsorship")
            )
        # Partner shouldn't be restricted
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
    def _filter_clean_invoices(self, since_date, to_date):
        """ For LSV/DD contracts, don't clean invoices that are in a
            Payment Order.
        """
        search = super()._filter_clean_invoices(since_date, to_date)
        invoices = self.env["account.invoice.line"].search(search).mapped("invoice_id")
        lsv_dd_invoices = self._get_lsv_dd_invoices(invoices)

        search.append(("invoice_id", "not in", lsv_dd_invoices.ids))
        return search

    def _get_invoice_lines_to_clean(self, since_date, to_date):
        """ For LSV/DD contracts, don't clean invoices that are in a
            Payment Order.
        """
        invoice_lines = super()._get_invoice_lines_to_clean(since_date, to_date)
        lsv_dd_invoices = self._get_lsv_dd_invoices(invoice_lines.mapped("invoice_id"))
        return invoice_lines.filtered(
            lambda line: line.invoice_id.id not in lsv_dd_invoices.ids
        )

    def _get_lsv_dd_invoices(self, invoices):
        lsv_dd_invoices = self.env["account.invoice"]
        for invoice in invoices:
            pay_line = self.env["account.payment.line"].search(
                [
                    ("move_line_id", "in", invoice.move_id.line_ids.ids),
                    ("order_id.state", "not in", ("draft", "cancel")),
                ]
            )
            if pay_line:
                lsv_dd_invoices += invoice

            # If a draft payment order exist, we remove the payment line.
            pay_line = self.env["account.payment.line"].search(
                [
                    ("move_line_id", "in", invoice.move_id.line_ids.ids),
                    ("order_id.state", "=", "draft"),
                ]
            )
            if pay_line:
                pay_line.unlink()
        return lsv_dd_invoices

    @api.multi
    def _on_sponsorship_finished(self):
        """ Called when a sponsorship is terminated or cancelled:
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

            # Deactivate pending invoice lines.
            opened = sponsorship.invoice_line_ids.mapped("invoice_id").filtered(
                lambda i: i.state == "open"
            )
            lsv_dd_invoices = self._get_lsv_dd_invoices(opened)
            (opened - lsv_dd_invoices).action_cancel()

    def check_mandate_needed(self, old_payment_modes):
        """ Change state of contract if payment is changed to/from LSV or DD.
        """
        for i, contract in enumerate(self):
            group = contract.group_id.with_context(lang="en_US")
            payment_name = group.payment_mode_id.name
            old_payment_name = old_payment_modes[i].with_context(lang="en_US").name
            if ("LSV" in payment_name or "Postfinance" in payment_name) and not (
                    "LSV" in old_payment_name or "Postfinance" in old_payment_name
            ):
                self.filtered(
                    lambda s: s.state in ["waiting", "active"]
                ).contract_waiting_mandate()
            elif ("LSV" in old_payment_name or "Postfinance"
                  in old_payment_name) and not ("LSV" in payment_name or
                                                "Postfinance" in payment_name):
                contract.mandate_valid()

    def _on_contract_lines_changed(self):
        inv_lines = self.env['account.invoice.line'].search(
            [('contract_id', 'in', self.ids),
             ('state', 'not in', ('paid', 'cancel'))]
        )

        invoices = inv_lines.mapped('invoice_id')
        opened = invoices.filtered(
            lambda i: i.state == "open"
        )
        lsv_dd_invoices = self._get_lsv_dd_invoices(opened)
        invoices_to_clean = invoices - lsv_dd_invoices
        invoices_to_clean.action_invoice_cancel()
        invoices_to_clean.action_invoice_draft()
        invoices_to_clean.env.clear()
        if self._update_invoice_lines(invoices_to_clean):
            invoices_to_clean.action_invoice_open()

    @api.multi
    def _update_invoice_lines(self, invoices):
        """ Update bvr_reference of invoices """
        success = super()._update_invoice_lines(invoices)
        for contract in self:
            ref = False
            bank_modes = (
                self.env["account.payment.mode"]
                    .with_context(lang="en_US")
                    .search(
                    ["|", ("name", "like", "LSV"), ("name", "like", "Postfinance")])
            )
            if contract.group_id.bvr_reference:
                ref = contract.group_id.bvr_reference
            elif contract.payment_mode_id in bank_modes:
                seq = self.env["ir.sequence"]
                ref = mod10r(seq.next_by_code("contract.bvr.ref"))
            invoices.write({"reference": ref})
        return success

    def _reconcile_open_amount(self):
        # Reconcile open amount of partner with contract invoices
        self.ensure_one()
        move_lines = self.env["account.move.line"].search(
            [
                ("partner_id", "=", self.partner_id.id),
                ("account_id.code", "=", "1050"),
                ("credit", ">", 0),
                ("reconciled", "=", False),
            ]
        )
        number_to_reconcile = int(sum(move_lines.mapped("credit") or [0])) // int(
            self.total_amount
        ) if self.total_amount else 0
        if number_to_reconcile:
            self.button_generate_invoices()
            invoices = self.invoice_line_ids.mapped("invoice_id").sorted("date_invoice")
            number = min(len(invoices), number_to_reconcile)
            invoices = invoices[:number]
            delay = datetime.datetime.now() + relativedelta(seconds=15)
            if invoices:
                invoices.with_delay(eta=delay).group_or_split_reconcile()
