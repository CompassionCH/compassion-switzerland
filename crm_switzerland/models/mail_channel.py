from odoo import models, _
from odoo.tools import html_escape


class MailChannel(models.Model):
    _inherit = 'mail.channel'

    def _define_command_log(self):
        return {'help': _('Log to partner (/log <partner_ref>)')}

    def _execute_command_log(self, **kwargs):
        partner_user = self.env.user.partner_id
        ref = kwargs['body'][4:].strip()
        messages = self.channel_message_ids.sorted('id')
        partner = self.env["res.partner"]
        if ref:
            partner = self.env["res.partner"].search([("ref", "=", ref)], limit=1)
        if not partner:
            partner = messages.mapped("author_id").filtered(
                lambda p: p != partner_user)
            if len(partner) > 1:
                self._send_transient_message(
                    partner_user, _(
                        "Please provide the reference of the partner on which you "
                        "would like to log the conversation.")
                )
                return
        if partner:
            # Move unassigned messages
            messages.filtered(lambda m: not m.author_id).write({
                "author_id": partner.id})
            # Log interaction
            description = ''.join(
                '%s: %s\n' % (
                message.author_id.name or self.anonymous_name, message.body)
                for message in messages
            )
            self.env["partner.log.other.interaction"].create({
                "partner_id": partner.id,
                "subject": self.livechat_channel_id.name,
                "other_type": "Livechat",
                "direction": "in",
                "body": description
            })
            self.name = self.name.replace(_("Visitor"), partner.name)
            msg = _('Log interaction in partner: <a href="#" data-oe-id="%s" data-oe-model="res.partner">%s</a>') % (partner.id, html_escape(partner.name))
            self._send_transient_message(partner_user, msg)
        else:
            self._send_transient_message(partner_user, _("Couldn't find a matching partner."))
