# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from pyquery import PyQuery

from odoo import _, fields, models
from odoo.tools import file_open

from odoo.addons.auth_signup.models.res_partner import now

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"
    signature = fields.Html(compute="_compute_signature")
    short_signature = fields.Html(compute="_compute_short_signature")
    signature_letter = fields.Html(compute="_compute_signature_letter")

    def action_reset_password(self):
        create_mode = bool(self.env.context.get("create_user"))
        # Only override the rest behavior, not normal signup
        if create_mode:
            super().action_reset_password()
        else:
            expiration = now(days=+1)
            self.mapped("partner_id").signup_prepare(
                signup_type="reset", expiration=expiration
            )
            config = self.env.ref(
                "partner_communication_switzerland.reset_password_email"
            )
            for user in self:
                self.env["partner.communication.job"].create(
                    {
                        "partner_id": user.partner_id.id,
                        "config_id": config.id,
                        "auto_send": True,
                    }
                )

    def _compute_signature(self):
        with file_open(
            "partner_communication_switzerland/static/html/signature.html"
        ) as tfile:
            template = PyQuery(tfile.read())
            phone = {
                "fr_CH": "+41 (0)24 434 21 24",
                "de_DE": "+41 (0)31 552 21 21",
                "it_IT": "+41 (0)31 552 21 24",
                "en_US": "+41 (0)31 552 21 25",
            }
            phone_link = {
                "fr_CH": "+41244342124",
                "de_DE": "+41315522121",
                "it_IT": "+41315522124",
                "en_US": "+41315522125",
            }
            facebook = {
                "fr_CH": "https://www.facebook.com/compassionsuisse/",
                "de_DE": "https://www.facebook.com/compassionschweiz/",
                "it_IT": "https://www.facebook.com/compassionsvizzera/",
                "en_US": "https://www.facebook.com/compassionsuisse/",
            }
            lang = self.env.lang or self._context.get("lang") or self.env.user.lang

            for user in self:
                employee = user.employee_ids[:1].with_context(bin_size=False)

                if employee:
                    base_url = (
                        self.env["ir.config_parameter"].sudo().get_param("web.base.url")
                    )
                    employee_image_url = f"{base_url}/employee/image/{employee.id}"

                    # Workaround that manually gets translation from the table,
                    # see T1693 and related PR for more information.
                    employee_job_title = self.env["ir.translation"]._get_source(
                        None, ("model",), lang, employee.job_title, employee.id
                    )

                    values = {
                        "name": f"{user.preferred_name} {user.lastname}"
                        if user.firstname
                        else _("The team of Compassion"),
                        "email": user.email if user.firstname else "info@compassion.ch",
                        "lang": lang,
                        "lang_short": lang[:2],
                        "team": _("and the team of Compassion")
                        if user.firstname
                        else "",
                        "job_title": employee_job_title or "",
                        "office_hours": _("mo-thu: 9am-2pm"),
                        "company_name": user.company_id.address_name,
                        "phone_link": phone_link.get(lang),
                        "phone": phone.get(lang),
                        "mobile": employee.mobile_phone,
                        "mobile_link": (employee.mobile_phone or "")
                        .replace(" ", "")
                        .replace("(0)", ""),
                        "facebook": facebook.get(lang),
                        "employee_image_url": employee_image_url,
                    }
                else:
                    values = {
                        "name": _("The team of Compassion"),
                        "email": "info@compassion.ch",
                        "lang": lang,
                        "lang_short": lang[:2],
                        "team": "",
                        "job_title": "",
                        "office_hours": _("mo-thu: 9am-2pm"),
                        "company_name": user.company_id.address_name,
                        "phone_link": phone_link.get(lang),
                        "phone": phone.get(lang),
                        "mobile": "",
                        "mobile_link": "",
                        "facebook": facebook.get(lang),
                    }

                if lang in ("fr_CH", "en_US"):
                    template.remove("#bern")
                else:
                    template.remove("#yverdon")
                if not employee.mobile_phone:
                    template.remove(".work_mobile")
                if not employee:
                    template.remove("#photo")
                user.signature = template.html().format(**values)

    def _compute_short_signature(self):
        for user in self:
            template = PyQuery(user.signature)
            user.short_signature = template("#short").html()

    def _compute_signature_letter(self):
        """Translate country in Signature (for Compassion Switzerland)"""
        for user in self:
            employee = user.employee_ids.sudo()
            signature = ""
            if len(employee) == 1:
                signature += employee.name + "<br/>"
                if employee.department_id:
                    signature += employee.department_id.name + "<br/>"
            signature += user.sudo().company_id.name.split(" ")[0] + " "
            signature += user.sudo().company_id.country_id.name
            user.signature_letter = signature
