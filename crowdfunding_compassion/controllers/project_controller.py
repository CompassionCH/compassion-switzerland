from datetime import datetime

from babel.dates import format_timedelta

from odoo.http import request, route, Controller


class ProjectController(Controller):

    # Demo route used to display demo project
    # TODO: Remove when developmnent is done
    @route("/project/demo", auth="public", website=True)
    def demo_project_page(self, **kwargs):
        demo_project = request.env.ref(
            "crowdfunding_compassion.demo_project_crowdfunding"
        ).sudo()

        return request.render(
            "crowdfunding_compassion.project_page",
            self._prepare_project_values(demo_project, **kwargs),
        )

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
                "text": f"{sponsorship.name} was sponsored",
                "image": sponsorship.child_id.portrait,
                "benefactor": sponsorship.correspondent_id.name,
                "date": sponsorship.activation_date or sponsorship.create_date.date(),
                "time_ago": self.get_time_ago(sponsorship.create_date),
                "anonymous": "TODO",
            }
            for sponsorship in project.sponsorship_ids
        ]

        donations = [
            {
                "type": "donation",
                "color": "grey",
                "text": f"{int(donation.price_unit / donation.product_id.list_price)} "
                f"{donation.product_id.crowdfunding_impact_text_passive}",
                "image": donation.product_id.product_tmpl_id.image_medium,
                "benefactor": donation.invoice_id.partner_id.name,
                "date": donation.invoice_id.date_invoice,
                "time_ago": self.get_time_ago(donation.invoice_id.create_date),
                "anonymous": donation.is_anonymous,
            }
            for donation in project.invoice_line_ids
        ]

        # Chronological list of sponsorships and fund donations for impact display
        impact = sorted(sponsorships + donations, key=lambda x: x["date"])

        fund = request.env['product.template'].sudo().search([
            ('activate_for_crowdfunding', '=', True),
            ("name", "like", project.product_id.product_tmpl_id.name)
        ])

        return {"project": project, "impact": impact, "fund": fund}

    # Utils
    def get_time_ago(self, date):
        return format_timedelta(date - datetime.now(), add_direction=True, locale="en")