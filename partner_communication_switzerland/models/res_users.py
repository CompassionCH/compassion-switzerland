# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import api, models, fields, _

from odoo.addons.auth_signup.models.res_partner import now
from odoo.tools import file_open
from pyquery import PyQuery

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"
    signature = fields.Html(compute="_compute_signature")

    @api.multi
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

    @api.multi
    def _compute_signature(self):
        with file_open("partner_communication_switzerland/static/html/signature.html")\
                as tfile:
            template = PyQuery(tfile.read())
            phone = {
                "fr_CH": "+41 (0)24 434 21 24",
                "de_DE": "+41 (0)31 552 21 21",
                "it_IT": "+41 (0)31 552 21 24",
                "en_US": "+41 (0)44 552 47 78"
            }
            phone_link = {
                "fr_CH": "+41244342124",
                "de_DE": "+41315522121",
                "it_IT": "+41315522124",
                "en_US": "+41445524778"
            }
            facebook = {
                "fr_CH": "https://www.facebook.com/compassionsuisse/",
                "de_DE": "https://www.facebook.com/compassionschweiz/",
                "it_IT": "https://www.facebook.com/compassionsvizzera/",
                "en_US": "https://www.facebook.com/compassionsuisse/"
            }
            for user in self:
                values = {
                    "user": user,
                    "name":
                    f"{user.preferred_name} {user.lastname}" if user.firstname else _(
                        "The team of Compassion"),
                    "email": user.email if user.firstname else "info@compassion.ch",
                    "lang": self.env.lang,
                    "lang_short": self.env.lang[:2],
                    "team": _("and the team of Compassion") if user.firstname else "",
                    "office_hours": _("mo-fri: 8am-4pm"),
                    "company_name": user.company_id.address_name,
                    "phone_link": phone_link.get(self.env.lang),
                    "phone": phone.get(self.env.lang),
                    "facebook": facebook.get(self.env.lang),
                }
                if self.env.lang in ("fr_CH", "en_US"):
                    template.remove("#bern")
                else:
                    template.remove("#yverdon")
                user.signature = template.html().format(**values)

    @api.multi
    def _compute_signature_letter(self):
        """ Translate country in Signature (for Compassion Switzerland) """
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
