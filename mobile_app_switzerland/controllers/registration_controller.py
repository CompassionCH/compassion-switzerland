##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import http
from odoo.http import request
from odoo.addons.mobile_app_connector.controllers.registration_controller import (
    RegistrationController,
)


class RegistrationControllerCH(RegistrationController):
    @http.route(
        ["/registration/page/<int:page>", "/registration/", "/registration/<partner_uuid>"],
        type="http",
        auth="public",
        website=True,
        sitemap=False
    )
    def registration(self, model_id=None, **kw):
        """Handle a wizard route.
        """
        partner_uuid = kw.get("partner_uuid")
        if partner_uuid:
            partner = request.env["res.partner"].sudo().search([("uuid", "=", partner_uuid)])
            if partner:
                kw["partner_id"] = partner.id
                kw["page"] = 2
        return super().registration(model_id, **kw)

    @http.route("/registration/confirm", type="http", auth="public", website=True,
                sitemap=False)
    def registration_confirm(self, **kw):
        hostname = request.env["wordpress.configuration"].sudo().get_host()
        storage = request.session.get("cms.form.res.users", {}).get("steps", {})
        source = storage.get(1, {}).get("source") or storage.get(2, {}).get("source")
        return request.render(
            "mobile_app_connector.mobile_registration_success",
            {"app_url": "https://" + hostname + "/app/Login",
             "source": source},
        )

    @http.route("/registration/success", type="http", auth="public", website=True,
                sitemap=False)
    def registration_success(self, **kwargs):
        """
        Return registration form
        """
        hostname = request.env["wordpress.configuration"].sudo().get_host()
        return request.redirect("https://" + hostname + "/app/Login")
