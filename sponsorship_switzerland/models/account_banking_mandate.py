##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, api


class AccountMandate(models.Model):
    _inherit = 'account.banking.mandate'

    @api.multi
    def validate(self):
        """Validate LSV/DD Contracts when mandate is validated."""
        super().validate()
        contracts = self._trigger_contracts('mandate')
        contracts.mandate_valid()
        return True

    @api.multi
    def cancel(self):
        """Set back contracts in waiting mandate state."""
        super().cancel()
        contracts = self._trigger_contracts('active') + self._trigger_contracts(
            'waiting')
        contracts.contract_waiting_mandate()
        return True

    @api.multi
    def _trigger_contracts(self, state):
        """ Fires a given transition on contracts in selected state. """
        contracts = self.env['recurring.contract']
        for mandate in self:
            contracts |= contracts.search(
                [('partner_id', 'child_of', mandate.partner_id.id),
                 ('state', '=', state)])
        return contracts
