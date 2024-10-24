##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models


class EndContractWizard(models.TransientModel):
    _inherit = "end.contract.wizard"

    generate_communication = fields.Boolean("Create depart communication")

    def end_contract(self):
        self.ensure_one()
        if self.generate_communication:
            exit_config = self.env.ref(
                "partner_communication_compassion.lifecycle_child_unplanned_exit"
            )
            self.contract_ids.with_context(
                default_object_ids=self.contract_ids.ids, default_auto_send=False
            ).send_communication(exit_config)

        return super().end_contract()
