##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Quentin Gigon
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo.http import request, route
from odoo.addons.website_event_compassion.controllers.events_controller import (
    EventsController,
)


class ProjectsController(EventsController):

    @route('/projects',
           auth="public",
           type="http",
           website=True)
    def get_projects_list(self, **kwargs):
        all_active_projects = request.env['crowdfunding.project'].search([])
        values = {}
        values.update({
            "project_list": [all_active_projects],
        })
        return request.render(
            "crowdfunding_compassion.project_list_view_template", values)
