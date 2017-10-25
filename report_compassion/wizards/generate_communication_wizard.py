# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from odoo import models, api, fields


class GenerateCommunicationWizard(models.TransientModel):
    _inherit = 'partner.communication.generate.wizard'

    product_id = fields.Many2one('product.product', 'Attach payment slip for')
    preprinted = fields.Boolean(
        help='Enable if you print on a payment slip that already has company '
             'information printed on it.'
    )

    @api.multi
    def generate(self):
        return super(GenerateCommunicationWizard, self.with_context(
            default_product_id=self.product_id.id,
            default_preprinted=self.preprinted
        )).generate()
