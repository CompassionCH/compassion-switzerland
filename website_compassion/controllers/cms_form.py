##############################################################################
#
#    Copyright (C) 2019-2020 Compassion CH (http://www.compassion.ch)
#    @author: Christopher Meier <dev@c-meier.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

"""
This file blocks all the routes defined automatically by cms_form.
"""

from odoo import http
from odoo.addons.cms_form.controllers.main import (
    CMSFormController,
    CMSWizardFormController,
    CMSSearchFormController,
)


class UwantedCMSFormController(CMSFormController):
    @http.route()
    def cms_form(self, model, model_id=None, **kw):
        return http.request.render("website.404")


class UnwantedCMSWizardFormController(CMSWizardFormController):
    @http.route()
    def cms_wiz(self, wiz_model, model_id=None, **kw):
        return http.request.render("website.404")


class UnwantedCMSSearchFormController(CMSSearchFormController):
    @http.route()
    def cms_form(self, model, **kw):
        return http.request.render("website.404")
