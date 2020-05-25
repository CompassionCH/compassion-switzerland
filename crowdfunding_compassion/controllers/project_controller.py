import base64
from datetime import datetime

from babel.dates import format_timedelta

from odoo import _
from odoo.http import request, route, Controller
from odoo.tools import file_open


class ProjectController(Controller):
    @route(
        ["/project/<model('crowdfunding.project'):project>"],
        auth="public",
        website=True,
    )
    def project_page(self, project, **kwargs):
        # Get project with sudo, otherwise some parts will be blocked from public
        # access, for example res.partner or account.invoice.line. This is
        # simpler and less prone to error than defining custom access and
        # security rules for each of them.
        return request.render(
            "crowdfunding_compassion.project_page",
            self._prepare_project_values(project.sudo(), **kwargs),
        )

    # TODO: test when we can create data for a project
    def _prepare_project_values(self, project, **kwargs):
        sponsorships = [
            {
                "type": "sponsorship",
                "color": "blue",
                "text": _("%s was sponsored") % sponsorship.child_id.preferred_name,
                "image": sponsorship.child_id.portrait,
                "benefactor": sponsorship.correspondent_id.name,
                "date": sponsorship.create_date,
                "time_ago": self.get_time_ago(sponsorship.create_date),
                "anonymous": False,
            }
            for sponsorship in project.sponsorship_ids
        ]

        donations = [
            {
                "type": "donation",
                "color": "grey",
                "text": f"{int(donation.quantity)} "
                f"{donation.product_id.crowdfunding_impact_text_passive}",
                "image": donation.product_id.image_medium,
                "benefactor": donation.invoice_id.partner_id.name,
                "date": donation.invoice_id.create_date,
                "time_ago": self.get_time_ago(donation.invoice_id.create_date),
                "anonymous": donation.is_anonymous,
            }
            for donation in project.invoice_line_ids.filtered(
                lambda l: l.state == "paid")
        ]

        # Chronological list of sponsorships and fund donations for impact display
        impact = sorted(sponsorships + donations, key=lambda x: x["date"], reverse=True)

        fund = project.product_id

        # check if current partner is owner of current project
        participant = request.env['crowdfunding.participant'].search([
            ("project_id", "=", project.id),
            ("partner_id", "in", (project.project_owner_id +
                                  request.env.user.partner_id).ids)
        ])

        return {
            "project": project,
            "impact": impact,
            "fund": fund,
            "participant": participant,
            "sponsor_banner": base64.b64encode(file_open(
                "crowdfunding_compassion/static/src/img/sponsor_children_banner.jpg",
                "rb").read()),
        }

    # Utils
    def get_time_ago(self, given_date):
        return format_timedelta(given_date - datetime.today(),
                                add_direction=True, locale=request.env.lang)
