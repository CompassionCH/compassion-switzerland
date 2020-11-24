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

from odoo import _, http, models
from odoo.http import request, route, Controller, local_redirect
from odoo.addons.cms_form.controllers.main import FormControllerMixin

from ..forms.project_creation_form import NoGoalException,\
    NegativeGoalException, InvalidDateException, InvalidLinkException
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website.models.ir_http import sitemap_qs2dom


class ProjectsController(Controller, FormControllerMixin):
    def sitemap_projects(env, rule, qs):
        projects = env['crowdfunding.project']
        dom = sitemap_qs2dom(qs, '/projects', projects._rec_name)
        dom += request.website.website_domain()
        for f in projects.search(dom):
            loc = '/project/%s' % slug(f)
            if not qs or qs.lower() in loc:
                yield {'loc': loc}

    @route("/projects", auth="public", website=True, sitemap=sitemap_projects)
    def get_projects_list(self, type=None, **kwargs):
        if request.website:
            website_id = request.website.id
            if website_id != 1:  # only for other site
                domain = request.website.website_domain()
                project_obj = request.env["crowdfunding.project"]

                # TODO connect pagination to backend -> CO-3213
                return request.render(
                    "crowdfunding_compassion.project_list_page",
                    {"projects": project_obj.sudo().get_active_projects(type=type).search(domain)},
                )
            else:
                raise werkzeug.exceptions.BadRequest()

    @route(['/projects/create', '/projects/create/page/<int:page>',
            '/projects/join/<int:project_id>'],
           auth="public",
           type="http",
           method='POST',
           website=True,
           no_sitemap=True)
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
           website=True, noindex=['robots', 'meta', 'header'],
           no_sitemap=True)
    def project_validation(self, project, **kwargs):
        return request.render(
            "crowdfunding_compassion.project_creation_confirmation_view_template",
            {
                "project": project.sudo(),
                "is_new": len(project.participant_ids) == 1
            })
