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
from odoo.addons.cms_form.controllers.main import FormControllerMixin


class ProjectsController(Controller, FormControllerMixin):

    @route('/projects', auth="public", website=True)
    def get_projects_list(self, **kwargs):
        values = {}
        project_obj = request.env['crowdfunding.project']
        values.update({
            "project_list": project_obj._get_active_projects_list(number=9),
        })
        return request.render(
            "crowdfunding_compassion.project_list_view_template", values)

    @route('/projects/create',
           auth="public",
           type="http",
           method='POST',
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
            }
        )
        project_creation_form = values["form"]
        if project_creation_form.form_success:
            result = request.render(
                "crowdfunding_compassion.project_creation_confirmation_view_template",
                {})
        else:
            result = request.render(
                "crowdfunding_compassion.project_creation_view_template", values)
        return result
