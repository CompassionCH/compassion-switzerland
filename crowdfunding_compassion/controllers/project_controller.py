from datetime import datetime

from babel.dates import format_timedelta

from odoo import _
from odoo.http import request, route, Controller


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
            "crowdfunding_compassion.presentation_page",
            self._prepare_project_values(project.sudo(), **kwargs),
        )

    @route(["/participant/<model('crowdfunding.participant'):participant>/"],
           type="http",
           auth="public",
           website=True)
    def participant(self, participant=None, **kwargs):
        project = participant.project_id.sudo()
        sponsorships, donations = self.get_sponsorships_and_donations(
            project.sponsorship_ids.filtered(
                lambda s: s.partner_id == participant.partner_id),
            project.invoice_line_ids.filtered(
                lambda line: line.partner_id == participant.partner_id
            )
        )
        values = {
            "participant": participant.sudo(),
            "project": project,
            "impact": self.get_impact(sponsorships, donations),
            "model": "participant",
            "base_url": request.website.domain
        }
        return request.render("crowdfunding_compassion.presentation_page", values)

    def _prepare_project_values(self, project, **kwargs):
        sponsorships, donations = self.get_sponsorships_and_donations(
            project.sponsorship_ids, project.invoice_line_ids)

        # check if current partner is owner of current project
        participant = request.env['crowdfunding.participant'].search([
            ("project_id", "=", project.id),
            ("partner_id", "in", (project.project_owner_id +
                                  request.env.user.partner_id).ids)
        ])

        return {
            "project": project,
            "main_object": project,
            "impact": self.get_impact(sponsorships, donations),
            "fund": project.product_id,
            "participant": participant,
            "model": "project",
            "base_url": request.website.domain
        }

    def get_sponsorships_and_donations(self, sponsorship_ids, invoice_line_ids):
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
