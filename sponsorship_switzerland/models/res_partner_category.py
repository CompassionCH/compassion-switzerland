# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from odoo import models, fields


class ResPartnerCategory(models.Model):
    """
    Warn user when making a sponsorship for sponsor that has a category.
    """
    _inherit = 'res.partner.category'

    warn_sponsorship = fields.Boolean()
