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
).read()), max_width=400)

SPONSOR_ICON = base64.b64encode(file_open(
    "crowdfunding_compassion/static/src/img/icn_children.png", "rb").read())

_logger = logging.getLogger(__name__)


def sponsorship_card_content():
    value = sum(request.env["crowdfunding.project"].sudo().search([]).mapped("number_sponsorships_reached"))
    return {"type": "sponsorship",
            "value": value,
            "name": _("Sponsor children"),
            "text": _("sponsored children") if value > 1 else _("sponsored child"),
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
        # Retrieve all projects open (deadline in the future)
        active_projects = request.env["crowdfunding.project"].sudo().get_active_projects(status='active')
        active_funds_data = []

        for fund in active_projects.mapped("product_id").filtered("activate_for_crowdfunding"):
            active_funds_data.append({
                "name": fund.crowdfunding_impact_text_active,
                "description": fund.crowdfunding_description,
                "icon_image": fund.image_medium or SPONSOR_ICON,
                # the header is a small image so we can compress it to save space
                "header_image":
                    compress_big_images(
                        fund.image_large,
                        max_width=400
                    ) if fund.image_large else SPONSOR_HEADER,
            })

        # populate the fund information depending on the impact type and the number of impact
        impact = {
            "sponsorship": sponsorship_card_content()
        }
        for fund in request.env['product.product'].sudo().search(
                [('product_tmpl_id.show_fund_together_homepage', '=', True)], order="total_fund_impact DESC"):
            impact_val = fund.product_tmpl_id.total_fund_impact
            if impact_val > 1:
                fund_text = fund.crowdfunding_impact_text_passive_plural
            else:
                fund_text = fund.crowdfunding_impact_text_passive_singular
            impact[fund.name] = {
                "type": "fund",
                "value": f"{impact_val:,}",
                "text": fund_text,
                "description": fund.crowdfunding_description,
                "icon_image": fund.image_medium or SPONSOR_ICON,
            }

        subheading = _("What we achieved so far")
        return {
            "projects": active_projects[:8],
            "impact": {k: v for k, v in impact.items() if v['value']},
            "active_funds": active_funds_data,
            "base_url": request.website.domain,
            "subheading": subheading,
        }
