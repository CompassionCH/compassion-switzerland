##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.addons.website_event_compassion.controllers.events_controller import (
    EventsController,
)

from odoo.http import request, route


class CrowdFundingWebsite(EventsController):

    @route(["/my_account"], type="http", auth="user", website=True)
    def my_account(self, form_id=None, **kw):
        """ Inject data for forms. """

        result = request.render("crowdfunding_compassion.myaccount_crowdfunding_view_template")
        return result
