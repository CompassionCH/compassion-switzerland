##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Stephane Eicher <seicher@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models


class HrEmployee(models.AbstractModel):
    _inherit = "hr.employee.base"

    job_title = fields.Char(translate=True)


class HrEmployeePrivatePartner(models.Model):
    _inherit = "hr.employee"

    private_partner_id = fields.Many2one(
        "res.partner",
        "Private Partner",
        groups="hr.group_hr_user",
        tracking=True,
        copy=False,
        domain="[('is_company', '=', False), ('parent_id', '=', False)]",
        help="Private contact of the employee, used as partner of the salary and "
        "expense entries. The work contact stays the professional identity "
        "(work email and phone, calendar, notifications).",
    )
    bank_account_id = fields.Many2one(
        domain="[('partner_id', '=', private_partner_id or work_contact_id), "
        "'|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )

    def _get_accounting_partner(self):
        """Partner of the salary and expense entries of the employee."""
        self.ensure_one()
        employee = self.sudo()
        return employee.private_partner_id or employee.work_contact_id

    def write(self, vals):
        # Changing the work contact moves the bank account to it and untrusts it:
        # keep the bank accounts that belong to the private partner.
        kept = {}
        if "work_contact_id" in vals:
            for employee in self.sudo():
                bank = employee.bank_account_id
                if bank and bank.partner_id == employee.private_partner_id:
                    kept[bank] = (bank.partner_id, bank.allow_out_payment)
        res = super().write(vals)
        for bank, (partner, allowed) in kept.items():
            bank = bank.sudo()
            if bank.partner_id != partner:
                bank.partner_id = partner
            if allowed and not bank.allow_out_payment and bank._user_can_trust():
                bank.allow_out_payment = True
        return res
