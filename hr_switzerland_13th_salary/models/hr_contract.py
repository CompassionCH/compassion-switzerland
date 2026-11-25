##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    @author: David Wulliamoz <dwulliamoz@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from datetime import date

from odoo import api, fields, models


class HrContract(models.Model):
    _inherit = "hr.contract"

    wage_fulltime = fields.Float(string="Full-time Wage", default=0)
    occupation_rate = fields.Float(string="Occupation Rate (%)", default=100.0)

    provision_13_salary = fields.Float(
        string="Accumulated 13th salary (Bruto)",
        compute="_compute_13_salary",
    )

    l10n_ch_thirteen_month = fields.Boolean(
        string="Has thirteen month", help="pay a thirteen salary per year"
    )

    lpp_amount = fields.Float(
        string="Pension Amount",
        help="monthly employee part (1/24 of yearly amount)",
    )

    @api.onchange("occupation_rate", "wage_fulltime")
    def _onchange_wage_rate_fulltime(self):
        for contract in self:
            contract.wage = contract.wage_fulltime * (contract.occupation_rate / 100)

    def _compute_13_salary(self):
        # Provision accumulated in the current half-year
        today = fields.Date.context_today(self)
        half_year_end = (
            date(today.year, 6, 30) if today.month <= 6 else date(today.year, 12, 31)
        )
        for contract in self:
            contract.provision_13_salary = contract._get_13_salary_provision(
                half_year_end
            )

    def _get_13_salary_provision(self, date_to):
        """Provision of the 13th salary (paid every six months) of the employee:
        PROVISION_13 of the done payslips of the half-year of `date_to` ending
        on or before `date_to`, minus CLEAR_PROVISION_13 already paid in it.
        Same computation as the salary rule TOTAL_PROVISION_13 with OCA
        payroll's `payslips.sum()`."""
        self.ensure_one()
        date_from = date_to.replace(month=1 if date_to.month <= 6 else 7, day=1)
        lines = self.env["hr.payslip.line"].search(
            [
                ("slip_id.employee_id", "=", self.employee_id.id),
                ("slip_id.state", "=", "done"),
                ("slip_id.date_from", ">=", date_from),
                ("slip_id.date_to", "<=", date_to),
                ("code", "in", ("PROVISION_13", "CLEAR_PROVISION_13")),
            ]
        )
        provision = 0.0
        for line in lines:
            sign = -1 if line.slip_id.credit_note else 1
            if line.code == "CLEAR_PROVISION_13":
                sign = -sign
            provision += sign * line.total
        return provision
