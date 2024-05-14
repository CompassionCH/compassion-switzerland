##############################################################################
#
#    Copyright (C) 2014-2024 Compassion CH (http://www.compassion.ch)
#    @author: Jérémie Lang
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    additional_ref = fields.Char(string="Additional Reference", readonly=True)
