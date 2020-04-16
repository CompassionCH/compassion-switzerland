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
        values = {}
        project_obj = request.env['crowdfunding.project']
        values.update({
            "project_list": [project_obj._get_3_active_projects()],
        })
        return request.render(
            "crowdfunding_compassion.project_list_view_template", values)
