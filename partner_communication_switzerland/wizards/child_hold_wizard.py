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


class ChildHoldWizard(models.TransientModel):
    """ Add return action for sub_sponsorship. """
    _inherit = 'child.hold.wizard'

    def _get_action(self, holds):
        action = super()._get_action(holds)
        if self.return_action == 'sub':
            sub_contract = self.env['recurring.contract'].browse(
                self.env.context.get('contract_id'))
            # Send the departure communication
            contract = sub_contract.parent_id
            action = self.env[
                'sds.subsponsorship.wizard'].send_sub_communication(
                    contract) or action
        return action
