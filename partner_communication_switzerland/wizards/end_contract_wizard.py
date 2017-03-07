# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import models, fields, api


class EndContractWizard(models.TransientModel):
    _inherit = 'end.contract.wizard'

    generate_communication = fields.Boolean(
        'Create depart communication')

    @api.multi
    def end_contract(self):
        self.ensure_one()
        child = self.child_id

        if self.generate_communication:
            exit_config = self.env.ref(
                'partner_communication_switzerland.'
                'lifecycle_child_unplanned_exit')
            self.contract_id.with_context(
                default_object_ids=child.id,
                default_auto_send=False).send_communication(exit_config)

        return super(EndContractWizard, self).end_contract()
