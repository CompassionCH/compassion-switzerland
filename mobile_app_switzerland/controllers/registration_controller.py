# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import http
from odoo.tools import config
from odoo.http import Controller, request


class RegistrationController(Controller):

    @http.route('/registration/success', type='http', auth='public',
                website=True)
    def registration_form(self, **kwargs):
        """
        Return registration form
        """
        hostname = config.get("wordpress_host")
        return request.redirect('https://' + hostname + '/app/Login')
