from datetime import datetime

from babel.dates import format_timedelta

from odoo import _
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website.models.ir_http import sitemap_qs2dom
from odoo.http import request, route, Controller
from odoo.addons.crowdfunding_compassion.controllers.\
    homepage_controller import sponsorship_card_content
import werkzeug


class ProjectController(Controller):
    def sitemap_projects(env, rule, qs):
        projects = env["crowdfunding.project"]
        dom = sitemap_qs2dom(qs, "/projects", projects._rec_name)
        dom += request.website.website_domain()
        dom += [("website_published", "=", True)]
        for f in projects.search(dom):
            loc = "/project/%s" % slug(f)
            if not qs or qs.lower() in loc:
                yield {"loc": loc}

    def sitemap_participant(env, rule, qs):
        projects = env["crowdfunding.participant"]
        dom = sitemap_qs2dom(qs, "/participant", projects._rec_name)
        dom += request.website.website_domain()
        dom += [("website_published", "=", True)]
        for f in projects.search(dom):
            loc = "/participant/%s" % slug(f)
            if not qs or qs.lower() in loc:
                yield {"loc": loc}

    @route(
        ["/project/<model('crowdfunding.project'):project>"],
        type='http',
        auth="public",
        website=True,
        sitemap=sitemap_projects
    )
    def project_page(self, page=1, project=None, **post):
        # Get project with sudo, otherwise some parts will be blocked from public
        # access, for example res.partner or account.invoice.line. This is
        # simpler and less prone to error than defining custom access and
        # security rules for each of them.
        if not project.can_access_from_current_website():
            raise werkzeug.exceptions.NotFound()
        if not project.website_published:
            return request.redirect("/projects")
        return request.render(
            "crowdfunding_compassion.presentation_page",
            self._prepare_project_values(project.sudo(), page=page, **post),
        )

    @route(["/participant/<model('crowdfunding.participant'):participant>/"],
           type="http",
           auth="public",
           website=True,
           sitemap=sitemap_participant)
    def participant(self, participant=None, **kwargs):
        if not participant.can_access_from_current_website():
            raise werkzeug.exceptions.NotFound()
        project = participant.project_id.sudo()
        if not project.website_published:
            return request.redirect("/projects")
        sponsorships, donations = self.get_sponsorships_and_donations(
            project.sponsorship_ids.filtered(
                lambda s: s.user_id == participant.partner_id),
            project.invoice_line_ids.filtered(
                lambda line: line.user_id == participant.partner_id
            )
        )
        values = {
            "participant": participant.sudo(),
            "main_object": participant.sudo(),
            "project": project,
            "impact": self.get_impact(sponsorships, donations),
            "model": "participant",
            "base_url": request.website.domain,
            "page": 2  # for jump to step 2 if donate from participant page
        }
        return request.render("crowdfunding_compassion.presentation_page", values)

    def _prepare_project_values(self, project, page, **kwargs):
        sponsorships, donations = self.get_sponsorships_and_donations(
            project.sponsorship_ids, project.invoice_line_ids)

        return {
            "project": project,
            "main_object": project,
            "impact": self.get_impact(sponsorships, donations),
            "fund": project.product_id,
            "sponsorship_card_content": sponsorship_card_content(),
            "participant": project.owner_participant_id,
            "model": "project",
            "base_url": request.website.domain,
            "page": page
        }

    def get_sponsorships_and_donations(self, sponsorship_ids, invoice_line_ids):
        sponsorships = [
            {
                "type": "sponsorship",
                "color": "blue",
                "text": _("%s was sponsored") % sponsorship.child_id.preferred_name,
                "image": sponsorship.child_id.portrait,
                "benefactor": sponsorship.correspondent_id.firstname,
                "date": sponsorship.create_date,
                "time_ago": self.get_time_ago(sponsorship.create_date),
                "anonymous": False,
                "quantity": 1,
            }
            for sponsorship in sponsorship_ids
        ]

        donations = [
            {
                "type": "donation",
                "color": "grey",
                "text": f"{int(donation.quantity)} "
                f"{donation.product_id.crowdfunding_impact_text_passive_plural}"
                if int(donation.quantity) > 1 else
                f"{int(donation.quantity)} "
                f"{donation.product_id.crowdfunding_impact_text_passive_singular}",
                "image": donation.product_id.image_medium,
                "benefactor": donation.invoice_id.partner_id.firstname,
                "date": donation.invoice_id.create_date,
                "time_ago": self.get_time_ago(donation.invoice_id.create_date),
                "anonymous": donation.is_anonymous,
                "quantity": int(donation.quantity)
            }
            for donation in invoice_line_ids.filtered(
                lambda l: l.state == "paid")
        ]
        return sponsorships, donations

    def get_impact(self, sponsorships, donations):
        # Chronological list of sponsorships and fund donations for impact display
        return sorted(sponsorships + donations, key=lambda x: x["date"], reverse=True)

    # Utils
    def get_time_ago(self, given_date):
        return format_timedelta(given_date - datetime.today(),
                                add_direction=True, locale=request.env.lang)
