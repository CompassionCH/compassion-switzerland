##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Quentin Gigon, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import _
from odoo.http import request, route, Controller, local_redirect
from odoo.addons.cms_form.controllers.main import FormControllerMixin

from ..forms.project_creation_form import NoGoalException


class ProjectsController(Controller, FormControllerMixin):
    @route("/projects", auth="public", website=True)
    def get_projects_list(self, **kwargs):
        project_obj = request.env["crowdfunding.project"]

        # TODO connect pagination to backend -> CO-3213
        return request.render(
            "crowdfunding_compassion.project_list_page",
            {"projects": project_obj.sudo().get_active_projects()},
        )

    @route(['/projects/create', '/projects/create/page/<int:page>',
            '/projects/join/<int:project_id>'],
           auth="public",
           type="http",
           method='POST',
           website=True)
    def project_creation(self, page=1, project_id=0, **kwargs):
        if project_id and page == 1:
            # Joining project can skip directly to step2
            page = 2
        values = {
            "form_model_key": "cms.form.crowdfunding.project.step" + str(page),
            "is_published": False,
            "page": page
        }
        # This allows the translation to still work on the page
        project_creation_form = self.get_form(
            "crowdfunding.project", int(project_id), **values)
        try:
            project_creation_form.form_process()
        except NoGoalException:
            request.website.add_status_message(_("Please define a goal"),
                                               type_='danger')
        values.update({
            "user": request.env.user,
            "form": project_creation_form,
            "funds": request.env["product.product"].sudo().search([
                ("activate_for_crowdfunding", "=", True)]),
            "product": project_creation_form.main_object.sudo().product_id,
        })
        project_creation_form = values["form"]
        if project_creation_form.form_success:
            # Force saving session, otherwise we lose values between steps
            request.session.save_request_data()
            return local_redirect(project_creation_form.form_next_url(
                project_creation_form.main_object))
        else:
            return request.render(
                "crowdfunding_compassion.project_creation_view_template", values,
                headers={'Cache-Control': 'no-cache'}
            )

    @route("/projects/create/confirm/<model('crowdfunding.project'):project>",
           auth="public",
           type="http",
           method='POST',
           website=True)
    def project_validation(self, project, **kwargs):
        return request.render(
            "crowdfunding_compassion.project_creation_confirmation_view_template",
            {"project": project.sudo(),
             "is_new": len(project.participant_ids) == 1}
        )
