##############################################################################
#
#    Copyright (C) 2014-2024 Compassion CH (http://www.compassion.ch)
#    @author: Jérémie Lang
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    plural_name = fields.Char(string="Plural product name", translate=True)
