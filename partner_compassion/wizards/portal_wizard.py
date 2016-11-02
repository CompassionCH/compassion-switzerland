# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import api, models
from openerp.tools import email_split


class PortalWizard(models.TransientModel):
    _inherit = 'portal.wizard'

    @api.multi
    def action_apply(self):
        """
        Add ambassador category to portal users
        """
        res = super(PortalWizard, self).action_apply()
        ambassador_id = self.env.ref(
            'partner_compassion.res_partner_category_ambassador').id
        self.mapped('user_ids.partner_id').write({
                'category_id': [(4, ambassador_id)]
            })
        return res


class PortalUser(models.TransientModel):
    _inherit = 'portal.wizard.user'

    @api.model
    def _create_user(self, wizard_user):
        """
        Override portal user creation to prevent sending e-mail to new user.
        """
        res_users = self.env['res.users'].with_context(
            noshortcut=True, no_reset_password=True)
        email = email_split(wizard_user.email)
        if email:
            email = email[0]
        else:
            email = wizard_user.partner_id.lastname.lower() + '@cs.local'
        values = {
            'email': email,
            'login': email,
            'partner_id': wizard_user.partner_id.id,
            'groups_id': [(6, 0, [])],
            'notify_email': 'none',
        }
        return res_users.create(values)

    @api.multi
    def _send_email(self):
        """ Never send invitation e-mails. """
        return True
