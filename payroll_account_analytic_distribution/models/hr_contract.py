# Copyright 2026 Compassion CH (http://www.compassion.ch)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class HrContract(models.Model):
    """The analytic distribution of a contract splits the salaries of the
    employee among analytic accounts (e.g. a key ADM 30 % / Fundraising 70 %)."""

    _name = "hr.contract"
    _inherit = ["hr.contract", "analytic.mixin"]
