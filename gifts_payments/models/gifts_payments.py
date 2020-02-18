import re

from odoo import models, fields, api, exceptions, _


class GiftsPayments(models.TransientModel):
    _name = "gifts.payments"

    gifts_ids_text = fields.Text("Gifts IDs")
    move_id = fields.Many2one(
        "account.move",
        string="Journal Entry",
        ondelete="cascade",
        help="The move of this entry line.",
        index=True,
        required=True,
        auto_join=True,
    )

    @api.multi
    def do_gifts_search(self):
        results = self.env["gifts.payments.results"].create(
            {"gifts_list": self.gifts_ids_text, "move": self.move_id.id}
        )

        return {
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "gifts.payments.results",
            "target": "new",
            "res_id": results.id,
            "context": self.env.context,
        }


class GiftsPaymentsResults(models.TransientModel):
    _name = "gifts.payments.results"
    _description = "Gifts payment result wizard"

    move_lines_gifts = fields.Many2many(
        comodel_name="account.move.line",
        string="Gifts paid",
        compute="_compute_move_lines",
    )

    gifts_list = fields.Text()
    move = fields.Many2one("account.move")

    @api.multi
    def _compute_move_lines(self):
        self.ensure_one()
        accounts = self.env["account.account"]
        ids = [int(i) for i in re.findall("[0-9]{3,6}", self.gifts_list)]
        gifts = self.env["sponsorship.gift"].browse(ids).exists()
        if len(ids) > len(gifts):
            missing_ids = set(ids) - set(gifts.ids)
            raise exceptions.UserError(
                _("Following gift ids were not found in database: %s")
                % ",".join([str(_id) for _id in missing_ids])
            )

        missing_gmc_ids = gifts.filtered(lambda g: not g.gmc_gift_id)
        if missing_gmc_ids:
            raise exceptions.UserError(
                _("Following gift ids have no gmc_gift_id : %s")
                % ",".join([str(_id) for _id in missing_gmc_ids.ids])
            )

        move_lines = gifts.mapped("payment_id.line_ids").filtered(
            lambda r: r.account_id.code == "2002"
        )

        debit = {
            "name": "gift",
            "ref": self.move.ref,
            "journal_id": self.move.journal_id.id,
            "currency_id": gifts.mapped("currency_usd").id,
            "credit": 0.0,
            "debit": sum(gifts.mapped("amount")),
            "date": self.move.date,
            "date_maturity": self.move.date,
            "amount_currency": sum(gifts.mapped("amount_us_dollars")),
            "partner_id": self.move.partner_id.id,
            "move_id": self.move.id,
            "account_id": move_lines.mapped("account_id").id,
        }

        credit = debit.copy()
        credit["debit"] = 0.0
        credit["credit"] = debit["debit"]
        credit["amount_currency"] = debit["amount_currency"] * -1
        credit["account_id"] = accounts.search([("code", "=", "2001")]).id

        #  write new lines in move
        self.move.write({"line_ids": [(0, 0, debit), (0, 0, credit)]})

        new_lines = self.move.line_ids.sorted("create_date")[-2:]
        line_id = new_lines.filtered(lambda r: r.account_id.code == "2002").id

        to_reconcile_list = move_lines.mapped("id")
        to_reconcile_list.append(line_id)
        to_reconcile = self.env["account.move.line"].browse(to_reconcile_list)

        self.move_lines_gifts = to_reconcile

    @api.multi
    def do_gifts_reconciliation(self):
        return self.move_lines_gifts.reconcile()
