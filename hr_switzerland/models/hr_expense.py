##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields


class HrExpense(models.Model):
    _inherit = "hr.expense"

    # Make product editable when expense is submitted
    product_id = fields.Many2one(
        states={"draft": [("readonly", False)], "submit": [("readonly", False)]},
        readonly=False,
    )

    @api.onchange("product_id")
    def _onchange_product_id(self):
        """
        Prevent changing amounts if expense is submitted.
        """
        if self.state == "draft":
            super()._onchange_product_id()
