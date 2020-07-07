#    Copyright (C) 2020 Compassion CH
#    @author: Quentin Gigon

from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = "product.template"

    activate_for_crowdfunding = fields.Boolean()
    crowdfunding_description = fields.Text(translate=True)
    crowdfunding_quantity_singular = fields.Char(translate=True, help="Ex: toilet")
    crowdfunding_quantity_plural = fields.Char(translate=True, help="Ex: toilets")
    crowdfunding_impact_text_active = fields.Char(
        translate=True, help="Ex: buildling toilets"
    )
    crowdfunding_impact_text_passive_singular = fields.Char(
        translate=True, help="Ex: toilet built"
    )
    crowdfunding_impact_text_passive_plural = fields.Char(
        translate=True, help="Ex: toilets built"
    )
    fund_selector_pre_description = fields.Char(
        translate=True, help="Ex: I want to give access to toilets for"
    )
    fund_selector_post_description = fields.Char(
        translate=True, help="Ex: children"
    )
    image_large = fields.Binary(
        "Large image", help="Image for header", attachment=True
    )
