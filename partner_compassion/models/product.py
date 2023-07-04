##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError


def check_fund_id(record):
    products = record.env[record._name].search(
        [("fund_id", "!=", 0), ("id", "!=", record.id)]
    )
    list_fund_id = [product.fund_id for product in products]
    if record.fund_id in list_fund_id:
        raise ValidationError(_("The Fund already exists in database."))
    if record.fund_id < 0:
        raise ValidationError(_("The Fund cannot have a negative value"))


class ProductTemplate(models.Model):
    _inherit = "product.template"
    _sql_constraints = [
        ("fund_id_unique", "unique(fund_id)", "The Fund already exists in database.")
    ]

    fund_id = fields.Integer(readonly=False)

    @api.constrains("fund_id")
    def _check_fund_id(self):
        check_fund_id(self)


class Product(models.Model):
    _inherit = "product.product"

    fund_id = fields.Integer(related="product_tmpl_id.fund_id")
