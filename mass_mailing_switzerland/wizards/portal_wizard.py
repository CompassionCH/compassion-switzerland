##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models


class PortalWizardUser(models.TransientModel):
    _inherit = "portal.wizard.user"

    @api.multi
    def action_apply(self):
        # Don't update mailchimp when creating user
        return super(
            PortalWizardUser, self.with_context(skip_mailchimp=True)).action_apply()
