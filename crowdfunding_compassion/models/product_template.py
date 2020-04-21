#    Copyright (C) 2020 Compassion CH
#    @author: Quentin Gigon

from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = "product.template"

    activate_for_crowdfunding = fields.Boolean()
    crowdfunding_description = fields.Text(translate=True)
    crowdfunding_impact_text = fields.Char(translate=True, help="Ex: toilets built")
