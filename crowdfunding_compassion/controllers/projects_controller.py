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

    @route('/together/projects/create',
           auth="user",
           type="http",
           method='POST',
           csrf=False,
           website=True)
    def project_creation_step1(self, **kwargs):
        values = kwargs.copy()
        values["form_model_key"] = "cms.form.crowdfunding.project"
        values.update({
            "is_published": False,
        })
        # This allows the translation to still work on the page
        project_creation_form = self.get_form("crowdfunding.project", **values)
        project_creation_form.form_process()
        values.update(
            {
                "user": request.env.user,
                "form": project_creation_form,
                "website_template": "crowdfunding_compassion.project_creation_view_template",
            }
        )
        project_creation_form = values["form"]
        if project_creation_form.form_success:
            result = request.render("crowdfunding_compassion.project_creation_confirmation_view_template", {})
        else:
            result = request.render(values["website_template"], values)
        return result
