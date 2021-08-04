##############################################################################
#
#    Copyright (C) 2021 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Jonathan Guerne <guernej@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import http, _
from odoo.http import request, Controller

from odoo.addons.cms_form.controllers.main import FormControllerMixin

_logger = logging.getLogger(__name__)


class OnboardingController(Controller, FormControllerMixin):

    @http.route(
        [
            "/onboarding/<string:onboarding_type>/unsubscribe/<string:onboarding_hash>"
        ],
        type="http", auth="public", methods=["GET", "POST"], website=True,
        sitemap=False)
    def onboarding_unsubscribe(self, onboarding_type, onboarding_hash, confirm_opt_out=False, **kwargs):

        if onboarding_type == "new_donors":
            return self._new_donors_onboarding_unsubscribe(onboarding_hash, confirm_opt_out)
        else:
            return http.request.render("website.404")

    def _new_donors_onboarding_unsubscribe(self, onboarding_hash, confirm_opt_out):
        partner = request.env["res.partner"].sudo().search(
            [("onboarding_new_donor_hash", "=", onboarding_hash)]
        )

        if not partner:
            return http.request.render("website.404")

        if not confirm_opt_out:
            return request.render(
                "partner_communication_switzerland.new_donors_onboarding_unsubscribe_template"
            )

        partner.opt_out = True

        return request.render(
            "partner_communication_switzerland.confirmation_onboarding_unsubscribe_template")
