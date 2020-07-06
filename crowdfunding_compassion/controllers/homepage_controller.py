import base64
from datetime import datetime

from odoo import _
from odoo.http import request, route, Controller
from odoo.tools.misc import file_open


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
        sponsor_banner = base64.b64encode(file_open(
            "crowdfunding_compassion/static/src/img/sponsor_children_banner.jpg", "rb"
        ).read())
        sponsor_icon = base64.b64encode(file_open(
            "crowdfunding_compassion/static/src/img/icn_children.png", "rb").read())

        impact = {
            "sponsorship": {
                "type": "sponsorship",
                "value": 0,
                "name": _("Sponsor children"),
                "text": _("sponsored child"),
                "description": _("""
For 42 francs a month, you're opening the way out of poverty for a child. Sponsorship
 ensures that the child is known, loved and protected. In particular, it gives the child
 access to schooling, tutoring, regular balanced meals, medical care and training in the
 spiritual field, hygiene, etc. Every week, the child participates in the activities of
 one of the project center of the 8,000 local churches that are partners of
 Compassion. They allow him or her to discover and develop his or her talents."""),
                "icon_image": sponsor_icon,
                "header_image": sponsor_banner
            }
        }

        for fund in active_funds:
            impact[fund.name] = {
                "type": "fund",
                "value": 0,
                "name": fund.crowdfunding_impact_text_active,
                "text": fund.crowdfunding_impact_text_passive_singular,
                "description": fund.crowdfunding_description,
                "icon_image": fund.image_medium or sponsor_icon,
                "header_image": fund.image_large or sponsor_banner,
            }

        for project in current_year_projects:
            impact["sponsorship"]["value"] += project.number_sponsorships_reached

            project_fund = project.product_id.name
            if project_fund in impact:
                impact[project_fund]["value"] += project.product_number_reached

        for fund in active_funds:
            if impact[fund.name]["value"] > 1:
                impact[fund.name]["text"] = fund.crowdfunding_impact_text_passive_plural

        if impact["sponsorship"]["value"] > 1:
            impact["sponsorship"]["name"] = _("Sponsor children")
            impact["sponsorship"]["text"] = _("sponsored children")

        return {
            "projects": project_obj.sudo().get_active_projects(limit=6),
            "impact": impact,
            "base_url": request.website.domain
        }
