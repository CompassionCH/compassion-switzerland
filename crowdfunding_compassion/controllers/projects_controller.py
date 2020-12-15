##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Quentin Gigon, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import werkzeug
from datetime import datetime, date

from odoo import _
from odoo.http import request, route, Controller, local_redirect
from odoo.addons.cms_form.controllers.main import FormControllerMixin

from ..forms.project_creation_form import NoGoalException,\
    NegativeGoalException, InvalidDateException, InvalidLinkException


class ProjectsController(Controller, FormControllerMixin):
    _project_post_per_page = 12

    @route(["/projects", "/projects/page/<int:page>"], auth="public", website=True,
           sitemap=False)
    def get_projects_list(self, type=None, page=1, year=None, status='all', **opt):
        if request.website:
            if request.website == request.env.ref(
                    "crowdfunding_compassion.crowdfunding_website").sudo():
                domain = request.website.website_domain()
                filters = list(filter(None, [
                    ("state", "!=", "draft"),
                    ("website_published", "=", True),
                    ("deadline", ">=", datetime(year, 1, 1)) if year else None,
                    ("deadline", "<=", datetime(year, 12, 31)) if year else None,
                    ("type", "=", type) if type else None,
                    ("deadline", ">=", date.today()) if status == 'active' else None,
                    ("deadline", "<", date.today()) if status == 'finish' else None,
                ]))
                filters += domain
                project_obj = request.env["crowdfunding.project"]
                total = project_obj.search_count(filters)

                pager = request.website.pager(
                    url='/projects',
                    total=total,
                    page=page,
                    step=self._project_post_per_page,
                    url_args={'type': type, 'status': status}
                )

                projects = project_obj.sudo().get_active_projects(
                    offset=(page - 1) * self._project_post_per_page, type=type,
                    domain=domain, limit=self._project_post_per_page, status=status)
                return request.render(
                    "crowdfunding_compassion.project_list_page",
                    {"projects": projects,
                     "status": status,
                     "type": type,
                     "pager": pager},
                )
            raise werkzeug.exceptions.BadRequest()

    @route(['/projects/create', '/projects/create/page/<int:page>',
            '/projects/join/<int:project_id>'],
           auth="public",
           type="http",
           method='POST',
           website=True,
           sitemap=False)
    def project_creation(self, page=1, project_id=0, **kwargs):
        if project_id and page == 1:
            # Joining project can skip directly to step2
            page = 2
        values = {
            "form_model_key": "cms.form.crowdfunding.project.step" + str(page),
            "is_published": False,
            "page": page
        }

        form = request.httprequest.form
        direction = form.get("wiz_submit")
        save = kwargs.get("save")
        if not direction and not save:
            values.update({"refresh": True})

        # This allows the translation to still work on the page
        project_creation_form = self.get_form(
            "crowdfunding.project", int(project_id), **values)

        if direction == "prev":
            return local_redirect(project_creation_form.form_next_url(
                project_creation_form.main_object))

        try:
            project_creation_form.form_process()
        except InvalidLinkException:
            request.website.add_status_message(
                _("A link you entered is incorrect"), type_="danger"
            )
        except InvalidDateException:
            request.website.add_status_message(
                _("Please select a valid date"), type_="danger"
            )
        except NoGoalException:
            request.website.add_status_message(
                _("Please define a goal"), type_="danger"
            )
        except NegativeGoalException:
            request.website.add_status_message(
                _("Please define a positive goal"), type_="danger"
            )
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
                headers={'Cache-Control': 'no-cache'})

    @route("/projects/create/confirm/<model('crowdfunding.project'):project>",
           auth="public",
           type="http",
           method='POST',
           website=True,
           sitemap=False)
    def project_validation(self, project, **kwargs):
        return request.render(
            "crowdfunding_compassion.project_creation_confirmation_view_template",
            {
                "project": project.sudo(),
                "is_new": len(project.participant_ids) == 1
            })
