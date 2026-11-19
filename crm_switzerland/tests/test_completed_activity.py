from odoo.tests import TransactionCase

from odoo.addons.mail.tools.discuss import Store


class TestCompletedActivity(TransactionCase):
    def _store_values(self, message):
        store = Store()
        message._to_store(store)
        return next(
            values
            for values in store.get_result()["mail.message"]
            if values["id"] == message.id
        )

    def test_done_activity_message_is_flagged(self):
        """The "... done" message of a completed activity is told apart from
        the other system notifications, which the chatter hides (T3610)."""
        partner = self.env["res.partner"].create({"name": "T3610 Partner"})
        activity = partner.activity_schedule(
            "mail.mail_activity_data_todo",
            summary="Call back",
            note="Ask about the letter",
        )
        messages, _next = activity._action_done(feedback="Called, all good")
        self.assertEqual(messages.message_type, "notification")
        self.assertTrue(self._store_values(messages)["is_completed_activity"])

        note = partner.message_post(body="A note", message_type="comment")
        self.assertFalse(self._store_values(note)["is_completed_activity"])
