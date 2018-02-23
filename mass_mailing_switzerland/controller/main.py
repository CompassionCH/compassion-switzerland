# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Sebastien Toth <popod@me.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import http
import odoo.addons.link_tracker.controller.main as main


class LinkTrackerCompassion(main.LinkTracker):
    @http.route()
    def full_url_redirect(self, code, **params):
        redirect_url = super(LinkTrackerCompassion, self).full_url_redirect(
            code, **params)

        # add customs params to target url
        if params:
            args = '&'.join([key + '=' + val
                             for key, val in params.iteritems()])
            redirect_url.location += args

        return redirect_url
