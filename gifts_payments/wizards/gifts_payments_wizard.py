from odoo import models, fields


class GiftsPayments(models.TransientModel):
    _name = "gifts.payments"
    _description = "Gift payments"

    gifts_ids_text = fields.Text("Gifts IDs")
    move_id = fields.Many2one(
        "account.move",
        string="Journal Entry",
        ondelete="cascade",
        help="The move of this entry line.",
        index=True,
        required=True,
        auto_join=True,
        readonly=False,
    )

    def do_gifts_search(self):
        results = self.env["gifts.payments.results"].create(
            {"gifts_list": self.mapped("gifts_ids_text"), "move": self.mapped("move_id.id")}
        )

        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "gifts.payments.results",
            "target": "new",
            "res_id": results.id,
            "context": self.env.context,
        }
