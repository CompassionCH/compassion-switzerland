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


class GenerateCommunicationWizard(models.TransientModel):
    _inherit = "partner.communication.generate.wizard"

    product_id = fields.Many2one(
        "product.product", "Attach payment slip for", readonly=False
    )

    def generate(self):
        return super(
            GenerateCommunicationWizard,
            self.with_context(
                default_product_id=self.product_id.id,
            ),
        ).generate()
