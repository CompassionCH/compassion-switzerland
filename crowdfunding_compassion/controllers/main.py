##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.http import Controller

from odoo.http import request, route


class CrowdFundingWebsite(Controller):

    @route(["/my_account"], type="http", auth="user", website=True)
    def my_account(self, form_id=None, **kw):
        """ Inject data for forms. """

        result = request.render("crowdfunding_compassion.myaccount_view_template")
        return result
