##############################################################################
#
#    Copyright (C) 2021 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Jonathan Guerne <jonathan.guerne@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging

from odoo import models, api, fields


class ProductProduct(models.Model):
    _name = "product.template"
    _inherit = "product.template"

    website_published = fields.Boolean(index=True)