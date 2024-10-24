##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


from odoo import models


class MailThread(models.AbstractModel):
    """
    Only allow employees as followers
    """

    _inherit = "mail.thread"

    def message_subscribe(self, partner_ids=None, channel_ids=None, subtype_ids=None):
        partners = self.env["res.partner"].browse(partner_ids)
        allowed = partners.mapped("user_ids").filtered(lambda u: not u.share)
        partner_ids = allowed.mapped("partner_id").ids
        return super().message_subscribe(partner_ids, channel_ids, subtype_ids)

    def _message_auto_subscribe_notify(self, partner_ids, template):
        partners = self.env["res.partner"].browse(partner_ids)
        allowed = partners.mapped("user_ids").filtered(lambda u: not u.share)
        partner_ids = allowed.mapped("partner_id").ids
        super()._message_auto_subscribe_notify(partner_ids, template)

    def _message_get_suggested_recipients(self):
        result = super()._message_get_suggested_recipients()
        to_remove = list()
        partner_obj = self.env["res.partner"]
        for message_id, suggestion in list(result.items()):
            if suggestion:
                partner = partner_obj.browse(suggestion[0][0])
                users = partner.mapped("user_ids").filtered(lambda u: not u.share)
                if not users:
                    to_remove.append(message_id)
        for message_id in to_remove:
            del result[message_id]
        return result

    def _mail_find_partner_from_emails(
        self,
        emails,
        records=None,
        force_create=False,
        extra_domain=False,
    ):
        if extra_domain is False:
            extra_domain = []
        # Search in archived partners for finding them
        extra_domain.append(("active", "in", [True, False]))
        return super()._mail_find_partner_from_emails(
            emails, records, force_create, extra_domain
        )
