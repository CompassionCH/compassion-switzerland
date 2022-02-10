##############################################################################
#
#    Copyright (C) 2021 Compassion CH (http://www.compassion.ch)
#    @author: Jonathan guerne <guernej@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
import urllib.parse

from odoo import models, fields, _

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    created_with_magic_link = fields.Boolean(default=False)

    def reset_password(self, login):
        """ retrieve the user corresponding to login (login or email),
            and reset their password

            case insensitive for email matching
        """
        try:
            return super().reset_password(login)
        except Exception:
            users = self.search([('email', '=ilike', login)])
            if len(users) != 1:
                raise
            return users.action_reset_password()


    def _wp_url_gift_child(self, child):
        self.ensure_one()
        partner = self.partner_id.with_context(lang=self.lang)

        if not child or not partner:
            return "#"

        data = {
            "firstname": partner.preferred_name,
            "pname": partner.name,
            "email": partner.email,
            "pstreet": partner.street,
            "pcity": partner.city,
            "pzip": partner.zip,
            "pcountry": partner.country_id.name,
            "sponsor_ref": partner.ref,
            "child_ref": child.local_id,
        }
        filter_data = {key: val for key, val in data.items() if val}
        params = urllib.parse.urlencode(filter_data)
        url = f"{_('https://compassion.ch/de/geschenkformular/')}?{params}"
        return url