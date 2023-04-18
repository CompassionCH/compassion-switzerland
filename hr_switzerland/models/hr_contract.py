##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    @author: David Wulliamoz <dwulliamoz@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields


class HrContract(models.Model):
    _inherit = "hr.contract"

    analytic_tag_id = fields.Many2one("account.analytic.tag", "Analytic tag")
