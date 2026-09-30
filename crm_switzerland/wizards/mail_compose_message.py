##############################################################################
#
#    Copyright (C) 2025 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Daniel Palumbo <dpalumbo@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import _, fields, models
from odoo.exceptions import AccessError, UserError


class MailComposeMessage(models.TransientModel):
    """
    Let the full composer edit an already posted log note in place instead of
    always posting a new message. Opened by the "Edit in full composer" chatter
    action (static/src/js/message_edit_full_note.js), which pre-fills the
    composer with the message's original HTML body.
    """

    _inherit = "mail.compose.message"

    edit_message_id = fields.Many2one(
        "mail.message",
        string="Message to edit",
        help="When set, saving the composer rewrites this existing message "
        "instead of posting a new one.",
    )

    def action_send_mail(self):
        editing = self.filtered("edit_message_id")
        for composer in editing:
            composer._update_edited_message()
        remaining = self - editing
        if remaining:
            return super(MailComposeMessage, remaining).action_send_mail()
        return {"type": "ir.actions.act_window_close"}

    def action_schedule_message(self, scheduled_date=False):
        if any(self.mapped("edit_message_id")):
            raise UserError(
                _("A message that is being edited cannot be scheduled for later.")
            )
        return super().action_schedule_message(scheduled_date=scheduled_date)

    def _update_edited_message(self):
        """Rewrite the body of the edited message, mirroring what the
        /mail/message/update_content controller does."""
        self.ensure_one()
        message = self.env["mail.message"]._get_with_access(
            self.edit_message_id.id, "create"
        )
        # The client-side gating of the edit action is not a security boundary,
        # so re-run the controller's own author/admin check here.
        if not message or not (
            message.sudo().is_current_user_or_guest_author or self.env.user._is_admin()
        ):
            raise AccessError(_("You are not allowed to edit this message."))
        thread = self.env[message.model].browse(message.res_id)
        thread.sudo()._message_update_content(message.sudo(), self.body or "")
