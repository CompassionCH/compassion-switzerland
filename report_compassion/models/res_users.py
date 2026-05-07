from markupsafe import Markup

from odoo import _, api, fields, models


class ResUsers(models.Model):
    _inherit = "res.users"
    signature = fields.Html(
        compute="_compute_signature", compute_sudo=True, store=False
    )
    short_signature = fields.Html(compute="_compute_short_signature", compute_sudo=True)
    signature_letter = fields.Html(
        compute="_compute_signature_letter", compute_sudo=True
    )
    image_url = fields.Char(compute="_compute_image_url", compute_sudo=True)

    @api.depends_context("lang")
    def _compute_signature(self):
        for user in self:
            render = self.env["ir.actions.report"]._render_template(
                "report_compassion.user_signature", {"object": user}
            )
            user.signature = render.decode("utf-8") if render else ""

    @api.depends_context("lang")
    def _compute_short_signature(self):
        for user in self:
            employee = user.employee_ids[:1]
            if employee:
                user.short_signature = f"{user.preferred_name} {user.lastname}"
            else:
                user.short_signature = _("The team of Compassion")

    @api.depends_context("lang")
    def _compute_signature_letter(self):
        """Translate country in Signature (for Compassion Switzerland)"""
        br = Markup("<br/>")
        for user in self:
            parts = []
            employee = user.employee_ids.sudo()
            if len(employee) == 1:
                parts.append(employee.name)
                if employee.department_id:
                    parts.append(employee.department_id.name)
            parts.append(
                user.sudo().company_id.name.split(" ")[0]
                + " "
                + user.sudo().company_id.country_id.name
            )
            user.signature_letter = br.join(parts)

    def _compute_image_url(self):
        for user in self:
            employee = user.employee_ids[:1]
            if employee:
                user.image_url = f"{user.get_base_url()}/employee/image/{employee.uuid}"
            else:
                user.image_url = f"{user.get_base_url()}/base/static/img/avatar.png"
