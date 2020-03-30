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

    @route(["/project_list"], type="http", auth="user", website=True, cors="*")
    def projects_list(self, form_id=None, **kw):
        """ Inject data for forms. """

        # result = request.redirect("/my/home")
        result = request.render("crowdfunding.project_list")
        return self._form_redirect(result, full_page=True)
