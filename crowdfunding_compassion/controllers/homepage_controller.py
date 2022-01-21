import base64
import time
from datetime import datetime
import logging

from odoo import _
from odoo.http import request, route, Controller
from odoo.tools.misc import file_open

from odoo.addons.website_compassion.tools.image_compression import compress_big_images

SPONSOR_HEADER = compress_big_images(base64.b64encode(file_open(
    "crowdfunding_compassion/static/src/img/sponsor_children_banner.jpg", "rb"
).read()), max_bytes_size=2e4, max_width=400)

SPONSOR_ICON = base64.b64encode(file_open(
    "crowdfunding_compassion/static/src/img/icn_children.png", "rb").read())

_logger = logging.getLogger(__name__)


def sponsorship_card_content():
    return {"type": "sponsorship",
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
            "icon_image": SPONSOR_ICON,
            "header_image": SPONSOR_HEADER
            }


class HomepageController(Controller):
    @route("/homepage", auth="public", website=True, sitemap=False)
    def homepage(self, **kwargs):
        return request.render(
            "crowdfunding_compassion.homepage_template",
            self._compute_homepage_context(),
        )

    @staticmethod
    def _compute_homepage_context():
        year = datetime.now().year
        project_obj = request.env["crowdfunding.project"].sudo()
        current_year_projects = project_obj.get_active_projects(year=year)
        active_funds = current_year_projects.mapped("product_id")
        impact = {
            "sponsorship": sponsorship_card_content()
        }
        for fund in active_funds:
            impact[fund.name] = {
                "type": "fund",
                "value": 0,
                "name": fund.crowdfunding_impact_text_active,
                "text": fund.crowdfunding_impact_text_passive_singular,
                "description": fund.crowdfunding_description,
                "icon_image": fund.image_medium or SPONSOR_ICON,
                # the header is a small image so we can compress it to save space
                "header_image":
                    compress_big_images(
                        fund.image_large,
                        max_bytes_size=2e4,
                        max_width=400
                    ) if fund.image_large else SPONSOR_HEADER,

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
            impact["sponsorship"]["text"] = _("sponsored children")

        subheading = _("What we achieved so far in {year}").format(year=year)

        return {
            "projects": current_year_projects[:8],
            "impact": {k: v for k, v in impact.items() if v['value']},
            "base_url": request.website.domain,
            "subheading": subheading,
        }
