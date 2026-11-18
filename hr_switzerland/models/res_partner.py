from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    private_employee_ids = fields.One2many(
        "hr.employee",
        "private_partner_id",
        "Employees (private partner)",
        groups="hr.group_hr_user",
    )

    def _compute_im_status(self):
        # hr_holidays_public reads user_ids.employee_id without sudo, which fails
        # for portal users (e.g. presence update on survey submit).
        return super(ResPartner, self.sudo())._compute_im_status()


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    def _compute_display_name(self):
        # Same masking as hr for the bank accounts of the private partners
        super()._compute_display_name()
        if self.env.user.has_group("hr.group_hr_user"):
            return
        for account in self.sudo().filtered("partner_id.private_employee_ids"):
            number = account.acc_number or ""
            account.sudo(self.env.su).display_name = (
                number[:2] + "*" * len(number[2:-4]) + number[-4:]
            )

    @api.model
    def _hr_switzerland_restrict_private_bank_accounts(self):
        """The hr rule hides the bank accounts of the work contacts from the
        users who are not HR officers: hide those of the private partners too.
        The rule is in a noupdate block of hr, so it is written from here."""
        rule = self.env.ref(
            "hr.ir_rule_res_partner_bank_internal_users", raise_if_not_found=False
        )
        domain = (
            "[('partner_id.employee_ids', '=', False), "
            "('partner_id.private_employee_ids', '=', False)]"
        )
        if rule and rule.sudo().domain_force != domain:
            rule.sudo().domain_force = domain
