# Copyright (c) 2018 Emanuel Cino <ecino@compassion.ch>

from odoo import models, api


class IrActionsReport(models.Model):

    _inherit = "ir.actions.report"

    @api.multi
    def behaviour(self):
        """
        Change behaviour to return user preference in priority.
        :return: report action for printing.
        """
        result = super().behaviour()

        # Retrieve user default values
        result.update(self._get_user_default_print_behaviour())
        return result
