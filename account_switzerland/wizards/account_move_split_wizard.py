from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError

ACTION_KEEP = "keep"
ACTION_MOVE = "move"
ACTION_SPLIT = "split"
ACTION_TOTAL = "total"


class AccountMoveSplitWizard(models.TransientModel):
    """Split one journal entry into two entries.

    The journal items flagged as "move" go to a copy of the entry, the ones
    flagged as "total" (receivable/payable of an invoice, for instance) are
    shared between both entries so that each of them stays balanced, together
    with their reconciliations.
    """

    _name = "account.move.split.wizard"
    _description = "Split a journal entry in two"

    move_id = fields.Many2one(
        "account.move", string="Journal Entry", required=True, readonly=True
    )
    company_currency_id = fields.Many2one(
        related="move_id.company_currency_id", string="Company Currency"
    )
    line_ids = fields.One2many(
        "account.move.split.wizard.line", "wizard_id", string="Journal Items"
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        move = self.env["account.move"].browse(
            res.get("move_id") or self.env.context.get("default_move_id")
        )
        if move and "line_ids" in fields_list:
            res["move_id"] = move.id
            locked_lines = self._get_locked_lines(move)
            res["line_ids"] = [
                Command.create(
                    {
                        "move_line_id": line.id,
                        "name": line.name or line.account_id.display_name,
                        "account_id": line.account_id.id,
                        "partner_id": line.partner_id.id,
                        "balance": line.balance,
                        "amount_currency": line.amount_currency,
                        "currency_id": line.currency_id.id,
                        "display_type": line.display_type,
                        "reconciled": bool(
                            line.matched_debit_ids or line.matched_credit_ids
                        ),
                        "locked": line in locked_lines,
                        "action": self._get_default_action(line),
                    }
                )
                for line in move.line_ids.sorted(lambda line: (line.sequence, line.id))
            ]
        return res

    @api.model
    def _get_default_action(self, line):
        if line.display_type == "payment_term":
            return ACTION_TOTAL
        if line.tax_line_id:
            return ACTION_SPLIT
        return ACTION_KEEP

    @api.model
    def _get_locked_lines(self, move):
        """Lines that are synchronized with a payment or a bank statement
        line and therefore must stay untouched in the original entry."""
        lines = self.env["account.move.line"]
        if move.origin_payment_id:
            lines |= move.origin_payment_id._seek_for_lines()[0]
        if move.statement_line_id:
            lines |= move.statement_line_id._seek_for_lines()[0]
        return lines

    # ------------------------------------------------------------------
    # Main action
    # ------------------------------------------------------------------
    def action_split(self):
        self.ensure_one()
        move = self.move_id
        self._check_move(move)

        # Everything below is a pure move of existing amounts between two
        # entries: the balance of each entry is verified at the end, and the
        # automatic synchronization of Odoo is disabled as it would otherwise
        # recompute the lines we are carefully splitting.
        self_ctx = self.with_context(
            check_move_validity=False,
            skip_invoice_sync=True,
            skip_account_move_synchronization=True,
        )
        new_move = self_ctx._apply_plan(self_ctx._compute_plan())

        return {
            "name": _("Split Journal Entries"),
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "view_mode": "list,form",
            "domain": [("id", "in", (move | new_move).ids)],
            "target": "current",
        }

    # ------------------------------------------------------------------
    # Checks
    # ------------------------------------------------------------------
    def _check_move(self, move):
        if move.inalterable_hash:
            raise UserError(
                _(
                    "The entry %s is hashed (inalterable) and therefore cannot "
                    "be split.",
                    move.display_name,
                )
            )
        if set(self.line_ids.move_line_id.ids) != set(move.line_ids.ids):
            raise UserError(
                _("The entry has been modified in the meantime, please start again.")
            )

    def _check_lines(self):
        wlines = self.line_ids
        to_move = wlines.filtered(lambda w: w.action == ACTION_MOVE)
        to_keep = wlines.filtered(lambda w: w.action == ACTION_KEEP)
        if not to_move:
            raise UserError(_("Select at least one journal item to move."))
        if not to_keep:
            raise UserError(
                _("At least one journal item must be kept in the current entry.")
            )
        for wline in wlines:
            line = wline.move_line_id
            label = line.name or line.account_id.display_name
            if wline.locked and wline.action != ACTION_KEEP:
                raise UserError(
                    _(
                        "The item '%s' is linked to a payment or a bank statement "
                        "and must be kept in the current entry.",
                        label,
                    )
                )
            if wline.action == ACTION_SPLIT and not line.tax_line_id:
                raise UserError(
                    _("Only tax items can be split proportionally ('%s').", label)
                )
            if wline.action == ACTION_TOTAL and (
                line.tax_line_id or line.display_type in ("line_section", "line_note")
            ):
                raise UserError(
                    _("The item '%s' cannot be used as a total item.", label)
                )

    @api.model
    def _check_partials_splittable(self, line, can_split_reconciled):
        partials = line.matched_debit_ids | line.matched_credit_ids
        if not partials:
            return
        label = line.name or line.account_id.display_name
        if not can_split_reconciled:
            raise UserError(
                _(
                    "The reconciled tax item '%s' cannot be split. "
                    "Unreconcile it first.",
                    label,
                )
            )
        if partials.exchange_move_id or self.env["account.move"].search_count(
            [("tax_cash_basis_rec_id", "in", partials.ids)]
        ):
            raise UserError(
                _(
                    "The reconciliation of '%s' generated exchange difference or "
                    "cash basis entries, which cannot be split automatically. "
                    "Unreconcile it first.",
                    label,
                )
            )

    # ------------------------------------------------------------------
    # Computation of the split
    # ------------------------------------------------------------------
    def _compute_plan(self):
        """Compute how every journal item is dispatched.

        :return: dict with
            moved: lines going entirely to the new entry
            splits: list of (line, vals_kept, vals_new) for shared lines
        """
        self._check_lines()
        move = self.move_id
        company_currency = move.company_currency_id
        wlines = self.line_ids
        moved = wlines.filtered(lambda w: w.action == ACTION_MOVE).move_line_id
        totals = wlines.filtered(lambda w: w.action == ACTION_TOTAL).move_line_id
        tax_lines = wlines.filtered(lambda w: w.action == ACTION_SPLIT).move_line_id

        splits = []  # (line, new_balance, new_amount_currency, new_base)
        moved_balance = sum(moved.mapped("balance"))
        moved_currency = {}
        for line in moved:
            moved_currency[line.currency_id] = (
                moved_currency.get(line.currency_id, 0.0) + line.amount_currency
            )

        # Taxes: shared in proportion of the moved base lines
        for tax_line in tax_lines:
            ratio = self._get_tax_moved_ratio(tax_line, moved)
            if not ratio:
                continue
            if ratio >= 1:
                moved |= tax_line
                moved_balance += tax_line.balance
                moved_currency[tax_line.currency_id] = (
                    moved_currency.get(tax_line.currency_id, 0.0)
                    + tax_line.amount_currency
                )
                continue
            self._check_partials_splittable(tax_line, False)
            balance = company_currency.round(tax_line.balance * ratio)
            amount_currency = tax_line.currency_id.round(
                tax_line.amount_currency * ratio
            )
            base = company_currency.round(tax_line.tax_base_amount * ratio)
            splits.append((tax_line, balance, amount_currency, base))
            moved_balance += balance
            moved_currency[tax_line.currency_id] = (
                moved_currency.get(tax_line.currency_id, 0.0) + amount_currency
            )

        # Total lines: absorb what is needed to balance the new entry
        needed = company_currency.round(-moved_balance)
        if not company_currency.is_zero(needed):
            if not totals:
                raise UserError(
                    _(
                        "The items to move are not balanced (difference of %s). "
                        "Flag at least one item (receivable, payable, ...) as "
                        "'Total' to share the difference between both entries, "
                        "or select balanced items.",
                        company_currency.round(moved_balance),
                    )
                )
            for line in totals:
                self._check_partials_splittable(line, True)
            splits += self._compute_total_splits(totals, needed, moved_currency)
        return {"moved": moved, "splits": splits, "totals": totals}

    @api.model
    def _get_tax_moved_ratio(self, tax_line, moved):
        """Share of the base of a tax line that is moved to the new entry."""
        tax = tax_line.tax_line_id
        base_lines = tax_line.move_id.line_ids.filtered(
            lambda line: line != tax_line
            and tax in line.tax_ids.flatten_taxes_hierarchy()
        )
        total = sum(abs(line.balance) for line in base_lines)
        if not total:
            return 0.0
        return sum(abs(line.balance) for line in base_lines & moved) / total

    @api.model
    def _compute_total_splits(self, totals, needed, moved_currency):
        """Share the amount `needed` over the total lines.

        :return: list of (line, new_balance, new_amount_currency, new_base)
        """
        company_currency = totals.move_id.company_currency_id
        total_balance = sum(totals.mapped("balance"))
        if (
            company_currency.compare_amounts(needed * total_balance, 0) <= 0
            or company_currency.compare_amounts(abs(needed), abs(total_balance)) >= 0
        ):
            raise UserError(
                _(
                    "The total items (%(total)s) cannot absorb the amount to "
                    "move (%(needed)s): the total must have the same sign and "
                    "be larger than the amount of the moved items.",
                    total=total_balance,
                    needed=needed,
                )
            )
        result = []
        remaining = needed
        for index, line in enumerate(totals):
            last = index == len(totals) - 1
            if last:
                balance = remaining
            else:
                balance = company_currency.round(needed * line.balance / total_balance)
            remaining -= balance
            # Amount in foreign currency
            currency = line.currency_id
            if currency == company_currency:
                amount_currency = balance
            elif len(totals) == 1 and set(moved_currency) <= {currency}:
                # Exactly the opposite of what is moved, in the same currency
                amount_currency = -moved_currency.get(currency, 0.0)
            else:
                amount_currency = currency.round(
                    line.amount_currency * balance / line.balance
                )
            if (
                currency.compare_amounts(
                    abs(amount_currency), abs(line.amount_currency)
                )
                >= 0
            ):
                raise UserError(
                    _(
                        "The item '%s' cannot absorb the amount to move.",
                        line.name or line.account_id.display_name,
                    )
                )
            result.append((line, balance, amount_currency, 0.0))
        return result

    # ------------------------------------------------------------------
    # Application of the split
    # ------------------------------------------------------------------
    def _apply_plan(self, plan):
        move = self.move_id
        moved = plan["moved"]
        splits = plan["splits"]
        totals = plan["totals"]
        state = move.state

        # 1. Keep the reconciliations of the shared total lines to rebuild
        # them later
        split_lines = self.env["account.move.line"].browse(
            [line.id for line, _b, _c, _t in splits if line in totals]
        )
        saved_partials = {}
        for line in split_lines:
            partials = line.matched_debit_ids | line.matched_credit_ids
            saved_partials[line] = [
                {
                    "other": (
                        partial.debit_move_id
                        if partial.credit_move_id == line
                        else partial.credit_move_id
                    ),
                    "line_is_debit": partial.debit_move_id == line,
                    "amount": partial.amount,
                    "debit_amount_currency": partial.debit_amount_currency,
                    "credit_amount_currency": partial.credit_amount_currency,
                }
                for partial in partials.sorted("id")
            ]
        full_reconciled = split_lines.filtered("full_reconcile_id")
        partials_to_remove = (
            split_lines.matched_debit_ids | split_lines.matched_credit_ids
        )
        partials_to_remove.unlink()

        # 2. Create the new (empty) entry
        new_move = self._create_new_move(move)

        # 3. Move the lines. Analytic items are created again when posting.
        moved.analytic_line_ids.unlink()
        # Odoo recomputes the amounts of the lines when their entry changes,
        # so we put back exactly what they were.
        saved_amounts = {
            line: line.read(
                [
                    "balance",
                    "amount_currency",
                    "price_unit",
                    "quantity",
                    "discount",
                ],
                load=False,
            )[0]
            for line in moved
        }
        moved.write({"move_id": new_move.id})
        for line, amounts in saved_amounts.items():
            amounts.pop("id")
            line.write(amounts)

        # 4. Share the lines
        new_lines = {}
        for line, balance, amount_currency, base in splits:
            vals = line.copy_data({"move_id": new_move.id})[0]
            for key in ("debit", "credit", "currency_rate", "matching_number"):
                vals.pop(key, None)
            vals.update(
                {
                    "balance": balance,
                    "amount_currency": amount_currency,
                    "move_id": new_move.id,
                }
            )
            if line.tax_line_id:
                vals["tax_base_amount"] = base
            new_line = self.env["account.move.line"].create(vals)
            new_lines[line] = new_line
            line.write(
                {
                    "balance": line.balance - balance,
                    "amount_currency": line.amount_currency - amount_currency,
                    **(
                        {"tax_base_amount": line.tax_base_amount - base}
                        if line.tax_line_id
                        else {}
                    ),
                }
            )
            if line.analytic_distribution and state == "posted":
                line.analytic_line_ids.unlink()
                line._create_analytic_lines()

        # 5. Rebuild the reconciliations
        for line, partials in saved_partials.items():
            if line in new_lines:
                self._restore_partials(line, new_lines[line], partials)
        self._restore_full_reconciles(full_reconciled, new_lines)

        # 6. Final verification of the balances
        self._check_balances(move | new_move)

        # 7. Put the new entry in the state of the original
        if state == "posted":
            new_move.with_context(skip_invoice_sync=True)._post(soft=False)
        elif state == "cancel":
            new_move.button_cancel()

        move.message_post(
            body=_(
                "This entry has been split. The moved journal items are now in %s.",
                new_move._get_html_link(),
            )
        )
        new_move.message_post(
            body=_(
                "This entry has been created by splitting %s.",
                move._get_html_link(),
            )
        )
        return new_move

    @api.model
    def _create_new_move(self, move):
        default = {
            "line_ids": [],
            "date": move.date,
            "ref": move.ref,
        }
        if move.is_invoice(include_receipts=True):
            default.update(
                {
                    "invoice_date": move.invoice_date,
                    "invoice_date_due": move.invoice_date_due,
                    "invoice_origin": move.invoice_origin,
                    "payment_reference": move.payment_reference,
                }
            )
        new_move = move.copy(default)
        # copy() applies the lock dates; the date must stay identical
        if new_move.date != move.date:
            raise UserError(
                _(
                    "The entry %s is in a locked period and cannot be split.",
                    move.display_name,
                )
            )
        return new_move

    @api.model
    def _restore_partials(self, line, new_line, partials):
        """Distribute the saved partial reconciliations of `line` over the
        line itself (up to its new residual capacity) and its new twin."""
        Partial = self.env["account.partial.reconcile"]
        company_currency = line.company_currency_id
        currency = line.currency_id
        cap_balance = abs(line.balance)
        cap_currency = abs(line.amount_currency)
        vals_list = []

        def add(target, other, line_is_debit, amount, line_cur, other_cur):
            if company_currency.is_zero(amount) and currency.is_zero(line_cur):
                return
            vals = {
                "debit_move_id": target.id if line_is_debit else other.id,
                "credit_move_id": other.id if line_is_debit else target.id,
                "amount": amount,
                "debit_amount_currency": line_cur if line_is_debit else other_cur,
                "credit_amount_currency": other_cur if line_is_debit else line_cur,
            }
            vals_list.append(vals)

        for partial in partials:
            other = partial["other"]
            line_is_debit = partial["line_is_debit"]
            amount = partial["amount"]
            line_cur = (
                partial["debit_amount_currency"]
                if line_is_debit
                else partial["credit_amount_currency"]
            )
            other_cur = (
                partial["credit_amount_currency"]
                if line_is_debit
                else partial["debit_amount_currency"]
            )
            ratio = 1.0
            if amount:
                ratio = min(ratio, cap_balance / amount)
            if line_cur:
                ratio = min(ratio, cap_currency / line_cur)
            if ratio >= 1:
                part_amount, part_line_cur, part_other_cur = amount, line_cur, other_cur
            elif ratio > 0:
                part_amount = min(company_currency.round(amount * ratio), cap_balance)
                part_line_cur = min(currency.round(line_cur * ratio), cap_currency)
                part_other_cur = other.currency_id.round(other_cur * ratio)
            else:
                part_amount = part_line_cur = part_other_cur = 0.0
            if part_amount or part_line_cur:
                add(
                    line,
                    other,
                    line_is_debit,
                    part_amount,
                    part_line_cur,
                    part_other_cur,
                )
            cap_balance -= part_amount
            cap_currency -= part_line_cur
            rest = (
                company_currency.round(amount - part_amount),
                currency.round(line_cur - part_line_cur),
                other.currency_id.round(other_cur - part_other_cur),
            )
            if any(rest):
                add(new_line, other, line_is_debit, *rest)
        Partial.create(vals_list)

    @api.model
    def _restore_full_reconciles(self, lines, new_lines):
        """Flag as fully reconciled the groups that were fully reconciled
        before the split and are still entirely paid."""
        FullReconcile = self.env["account.full.reconcile"]
        for line in lines:
            for candidate in (line, new_lines.get(line)):
                if not candidate or candidate.full_reconcile_id:
                    continue
                group = candidate._all_reconciled_lines()
                if (
                    not group.full_reconcile_id
                    and group.matched_debit_ids | group.matched_credit_ids
                    and all(group.mapped("reconciled"))
                ):
                    partials = group.matched_debit_ids | group.matched_credit_ids
                    FullReconcile.create(
                        {
                            "partial_reconcile_ids": [
                                Command.link(p.id) for p in partials
                            ],
                            "reconciled_line_ids": [Command.link(m.id) for m in group],
                        }
                    )
                    self.env["account.partial.reconcile"]._update_matching_number(group)

    @api.model
    def _check_balances(self, moves):
        for move in moves:
            if not move.company_currency_id.is_zero(
                sum(move.line_ids.mapped("balance"))
            ):
                raise UserError(
                    _(
                        "The entry %s would not be balanced after the split.",
                        move.display_name,
                    )
                )
            if not move.line_ids:
                raise UserError(_("An entry cannot be left without any item."))


class AccountMoveSplitWizardLine(models.TransientModel):
    _name = "account.move.split.wizard.line"
    _description = "Journal item to dispatch when splitting an entry"
    _order = "id"

    wizard_id = fields.Many2one(
        "account.move.split.wizard", required=True, ondelete="cascade"
    )
    move_line_id = fields.Many2one("account.move.line", required=True, readonly=True)
    name = fields.Char(readonly=True)
    account_id = fields.Many2one("account.account", readonly=True)
    partner_id = fields.Many2one("res.partner", readonly=True)
    company_currency_id = fields.Many2one(
        related="wizard_id.company_currency_id", readonly=True
    )
    balance = fields.Monetary(currency_field="company_currency_id", readonly=True)
    currency_id = fields.Many2one("res.currency", readonly=True)
    amount_currency = fields.Monetary(currency_field="currency_id", readonly=True)
    display_type = fields.Char(readonly=True)
    reconciled = fields.Boolean(readonly=True)
    locked = fields.Boolean(readonly=True)
    action = fields.Selection(
        [
            (ACTION_KEEP, "Keep"),
            (ACTION_MOVE, "Move to the new entry"),
            (ACTION_SPLIT, "Split (taxes)"),
            (ACTION_TOTAL, "Total (adapt and split)"),
        ],
        required=True,
        default=ACTION_KEEP,
    )
