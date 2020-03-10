##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = "product.template"

    fund_id = fields.Integer(size=4)


class Product(models.Model):
    _inherit = "product.product"

    fund_id = fields.Integer(related="product_tmpl_id.fund_id")
