##############################################################################
#
#    Copyright (C) 2021 Compassion CH (http://www.compassion.ch)
#    @author: Jonathan guerne <guernej@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import models, fields

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
