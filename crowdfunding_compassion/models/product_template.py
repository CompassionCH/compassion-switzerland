#    Copyright (C) 2020 Compassion CH
#    @author: Quentin Gigon

from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = "product.template"

    activate_for_crowdfunding = fields.Boolean()
    impact_type = fields.Selection([
        ("standard", "Standard"),
        ("large", "Large impact project")
    ],
        help="Use large impact if the project goals should be displayed in terms "
             "of percentage.",
        default="standard"
    )
    crowdfunding_description = fields.Text(
        translate=True,
        help="Description of the fund visible on Homepage"
    )
    crowdfunding_quantity_singular = fields.Char(
        translate=True,
        help="Visible when choosing donation quantity 1 or when "
             "displaying project goal equivalence for 1 quantity.")
    crowdfunding_quantity_plural = fields.Char(
        translate=True,
        help="Visible when choosing donation quantity or setting project goal "
             "for large impact projects.")
    crowdfunding_impact_text_active = fields.Char(
        translate=True, help="Fund title on TOGETHER"
    )
    crowdfunding_impact_text_passive_singular = fields.Char(
        translate=True,
        help="Shown on barometers when impact is 1 or less."
    )
    crowdfunding_impact_text_passive_plural = fields.Char(
        translate=True,
        help="Shown on barometers when impact is more than 1."
    )
    fund_selector_pre_description = fields.Char(
        translate=True,
        help="Shown when setting the goal of a project, before the quantity field."
    )
    fund_selector_post_description = fields.Char(
        translate=True,
        help="Shown when setting the goal of a project, after the quantity field."
    )
    image_large = fields.Binary(
        "Large image", help="Image for header", attachment=True
    )
