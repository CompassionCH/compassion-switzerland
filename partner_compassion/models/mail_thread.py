
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


from odoo import models, api, tools


class MailThread(models.AbstractModel):
    """
    Only allow employees as followers
    """
    _inherit = 'mail.thread'

    @api.multi
    def message_subscribe(self, partner_ids=None, channel_ids=None,
                          subtype_ids=None, force=True):
        partners = self.env['res.partner'].browse(partner_ids)
        allowed = partners.mapped('user_ids').filtered(lambda u: not u.share)
        partner_ids = allowed.mapped('partner_id.id')
        return super().message_subscribe(
            partner_ids, channel_ids, subtype_ids, force)

    @api.multi
    def _message_auto_subscribe_notify(self, partner_ids):
        partners = self.env['res.partner'].browse(partner_ids)
        allowed = partners.mapped('user_ids').filtered(lambda u: not u.share)
        partner_ids = allowed.mapped('partner_id.id')
        super()._message_auto_subscribe_notify(partner_ids)

    @api.multi
    def message_get_suggested_recipients(self):
        result = super().message_get_suggested_recipients()
        to_remove = list()
        partner_obj = self.env['res.partner']
        for message_id, suggestion in list(result.items()):
            if suggestion:
                partner = partner_obj.browse(suggestion[0][0])
                users = partner.mapped('user_ids').filtered(
                    lambda u: not u.share)
                if not users:
                    to_remove.append(message_id)
        for message_id in to_remove:
            del result[message_id]
        return result

    @api.multi
    def _find_partner_from_emails(self, emails, res_model=None, res_id=None,
                                  check_followers=True, force_create=False,
                                  exclude_aliases=True):

        partner_ids = super()._find_partner_from_emails(
            emails, res_model, res_id, check_followers,
            force_create, exclude_aliases)

        respartner = self.env['res.partner'].sudo()
        count = 0
        for contact in emails:
            if not partner_ids[count]:
                partner_id = False
                email_address = tools.email_split(contact)
                if not email_address:
                    partner_ids.append(partner_id)
                    continue
                partner_id = respartner.search(
                    ['&', ('active', '=', False),
                          ('email', '=ilike', email_address[0])], limit=1)
                partner_ids[count] = partner_id.id
            count += 1

        return partner_ids
