# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Christopher Meier <dev@c-meier.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import http, _
from odoo.http import request

from odoo.addons.cms_form.controllers.main import FormControllerMixin


class ChildProtectionCharterController(http.Controller, FormControllerMixin):
    """
    All the route controllers to agree to the child protection charter.
    """

    @http.route(route='/partner/<string:reg_uid>/child-protection-charter',
                auth='public', website=True)
    def child_protection_charter_agree(self, reg_uid, form_id=None, **kwargs):
        # Need sudo() to bypass domain restriction on res.partner for anonymous
        # users.
        partner = request.env['res.partner'].sudo().search([
            ('uuid', '=', reg_uid)])

        if not partner:
            return request.redirect('/')

        values = kwargs.copy()

        form_model_key = 'cms.form.partner.child.protection.charter'
        # Do not use self.get_form() because it does not have sufficient rights
        # to search for the partner object (by the id).
        child_protection_form = request.env[form_model_key].form_init(
            request, main_object=partner, **values)
        child_protection_form.form_process()

        partner.env.invalidate_all()
        values.update({
            'partner': partner,
            'child_protection_form': child_protection_form,
        })

        if partner.has_agreed_child_protection_charter:
            values = {
                'confirmation_title': _("Thank you!"),
                'confirmation_message': _(
                    "We successfully received your agreement to the Child "
                    "Protection Charter.")
            }
            return request.render(
                'partner_compassion.'
                'child_protection_charter_confirmation_page', values)
        else:
            return request.render(
                'partner_compassion.child_protection_charter_page', values)
