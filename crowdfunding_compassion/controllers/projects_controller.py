##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Quentin Gigon
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo.http import request, route, Controller


class ProjectsController(Controller):

    @route('/together/projects',
           auth="public",
           type="http",
           website=True)
    def get_projects_list(self, **kwargs):
        values = {}
        project_obj = request.env['crowdfunding.project']
        projects = project_obj._get_active_projects_rows()
        first_row = []
        second_row = []
        third_row = []
        for project in projects:
            if len(first_row) < 3:
                first_row.append(project)
            elif len(second_row) < 3:
                second_row.append(project)
            else:
                third_row.append(project)

        values.update({
            "project_list": [first_row, second_row, third_row],
        })
        return request.render(
            "crowdfunding_compassion.project_list_view_template", values)
