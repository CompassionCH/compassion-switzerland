from odoo import models

from odoo.addons.mail.tools.discuss import Store


class MailMessage(models.Model):
    _inherit = "mail.message"

    def _to_store(self, store: Store, /, **kwargs):
        # Lets the chatter filter show the "... done" messages of completed
        # activities on their own, apart from the other system notifications
        # (T3610).
        res = super()._to_store(store, **kwargs)
        for message in self:
            store.add(
                message,
                {"is_completed_activity": bool(message.mail_activity_type_id)},
            )
        return res
