from datetime import datetime

from odoo import _
from odoo.http import request, route, Controller


class HomepageController(Controller):
    @route("/homepage", auth="public", website=True)
    def homepage(self, **kwargs):
        return request.render(
            "crowdfunding_compassion.homepage_template",
            self._compute_homepage_context(datetime.now().year),
        )

    def _compute_homepage_context(self, year, **kwargs):
        project_obj = request.env["crowdfunding.project"]
        fund_obj = request.env["product.product"]

        current_year_projects = project_obj.sudo().get_active_projects(year=year)
        active_funds = fund_obj.sudo().search(
            [("activate_for_crowdfunding", "=", True)]
        )

        impact = {
            "sponsorship": {
                "value": 0,
                "name": _("Sponsor children"),
                "text": _("sponsored children"),
                "description": _("Description to be added"),
                "image": "crowdfunding_compassion/static/src/img/defaut_fund_icon.png",
            }
        }

        for fund in active_funds:
            impact[fund.name] = {
                "value": 0,
                "name": fund.crowdfunding_impact_text_active,
                "text": fund.crowdfunding_impact_text_passive,
                "description": fund.description,
                "image": fund.image_medium
                or "crowdfunding_compassion/static/src/img/defaut_fund_icon.png",
            }

        for project in current_year_projects:
            impact["sponsorship"]["value"] += project.number_sponsorships_reached

            project_fund = project.product_id.name
            if project_fund in impact:
                impact[project_fund]["value"] += project.product_number_reached

        return {
            "projects": project_obj.sudo().get_active_projects(limit=6),
            "impact": impact,
        }
