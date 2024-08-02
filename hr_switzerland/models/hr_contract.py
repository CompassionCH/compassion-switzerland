##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    @author: David Wulliamoz <dwulliamoz@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, fields, models

import odoo.addons.decimal_precision as dp


class HrContract(models.Model):
    _inherit = "hr.contract"

    analytic_tag_id = fields.Many2one("account.analytic.tag", "Analytic tag")
    wage_fulltime = fields.Float(
        string="Full-time Wage", digits="Account", default=0
    )
    occupation_rate = fields.Float(
        string="Occupation Rate (%)", digits="Account", default=100.0
    )

    provision_13_salary = fields.Float(
        string="Accumulated 13th salary (Bruto)",
        compute="_compute_13_salary",
        digits="Account",
    )

    l10n_ch_thirteen_month = fields.Boolean(
        string="Has thirteen month", help="pay a thirteen salary per year"
    )

    lpp_amount = fields.Float(
        string="Pension Amount",
        digits="Account",
        help="monthly employee part (1/24 of yearly amount)",
    )

    @api.onchange("occupation_rate", "wage_fulltime")
    def _onchange_wage_rate_fulltime(self):
        for contract in self:
            contract.wage = contract.wage_fulltime * (contract.occupation_rate / 100)

    def _compute_13_salary(self):
        account_id = self.env.ref("l10n_ch_hr_payroll.PROVISION_13").account_credit.id
        for contract in self:
            move_lines = self.env["account.move.line"].search(
                [
                    ("partner_id", "=", contract.employee_id.address_home_id.id),
                    ("account_id", "=", account_id),
                ]
            )
            contract.provision_13_salary = sum(move_lines.mapped("credit")) - sum(
                move_lines.mapped("debit")
            )
