##############################################################################
#
#    Copyright (C) 2021 Compassion CH (http://www.compassion.ch)
#    @author: Jonathan guerne <guernej@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import models,_

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    def reset_password(self, login):
        """ retrieve the user corresponding to login (login or email),
            and reset their password

            case insensitive for email matching
        """
        users = self.search([('login', '=', login)])
        if not users:
            users = self.search([('email', '=ilike', login)])
        if len(users) != 1:
            raise Exception(_('Reset password: invalid username or email'))
        return users.action_reset_password()
