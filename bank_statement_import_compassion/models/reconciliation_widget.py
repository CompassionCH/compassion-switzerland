##############################################################################
#
#    Copyright (C) 2014-2024 Compassion CH (http://www.compassion.ch)
#    @author: Jérémie Lang
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import _, api, models


class AccountReconciliation(models.AbstractModel):
    _inherit = "account.reconciliation.widget"

    def _get_statement_line(self, st_line):
        data = super()._get_statement_line(st_line)
        data["additional_ref"] = st_line.additional_ref
        return data
