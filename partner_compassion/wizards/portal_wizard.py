# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models
from odoo.tools import email_split


class PortalWizard(models.TransientModel):
    _inherit = 'portal.wizard'


class PortalUser(models.TransientModel):
    _inherit = 'portal.wizard.user'

    @api.multi
    def _create_user(self):
        """
        Override portal user creation to prevent sending e-mail to new user.
        """
        res_users = self.env['res.users'].with_context(
            noshortcut=True, no_reset_password=True)
        email = email_split(self.email)
        if email:
            email = email[0]
        else:
            email = self.partner_id.lastname.lower() + '@cs.local'
        values = {
            'email': email,
            'login': email,
            'partner_id': self.partner_id.id,
            'groups_id': [(6, 0, [])],
            'notify_email': 'none',
        }
        return res_users.create(values)

    @api.multi
    def _send_email(self):
        """ Never send invitation e-mails. """
        return True
