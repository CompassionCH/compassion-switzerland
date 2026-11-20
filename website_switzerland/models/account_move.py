from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _invoice_paid_hook(self):
        """Paying the fee or the trip of a registration ticks its task off,
        whatever the way it was paid (portal, payment slip, by hand)."""
        res = super()._invoice_paid_hook()
        tasks = self.env["event.registration.task.rel"].sudo()
        for xmlid, invoice_field in (
            ("task_down_payment", "down_payment_id"),
            ("task_full_payment", "trip_invoice_id"),
        ):
            tasks.search(
                [
                    (f"registration_id.{invoice_field}", "in", self.ids),
                    ("task_id", "=", self.env.ref(f"website_switzerland.{xmlid}").id),
                    ("done", "=", False),
                ]
            ).write({"done": True})
        return res
