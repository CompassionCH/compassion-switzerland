from datetime import datetime

from odoo.http import request, route, Controller


class HomepageController(Controller):
    # Demo route used to display demo project
    @route("/home", auth="public", website=True)
    def homepage(self, **kwargs):
        context = {
            "funds": [
                "Building safe toilets",
                "Help mothers and babies",
                "Provide medical care",
                "Sponsor a child",
            ],
            "impact": self._compute_projects_impact(datetime.now().year),
        }

        return request.render("crowdfunding_compassion.homepage", context)

    def _compute_projects_impact(self, year, **kwargs):
        projects = (
            request.env["crowdfunding.project"]
            .sudo()
            .search(
                [
                    ("deadline", ">=", datetime(year, 1, 1)),
                    ("deadline", "<=", datetime(year, 12, 31)),
                ]
            )
        )

        impact = {
            "sponsorship": 0,
            "toilets": 0,
            "csp": 0,
            "other": 0,
        }

        toilets_fund = request.env.ref(
            "sponsorship_switzerland.product_template_fund_toilets"
        )
        csp_fund = request.env.ref("sponsorship_switzerland.product_template_fund_csp")

        for project in projects:
            impact["sponsorships"] += project.number_sponsorships_reached

            if project.product_id == toilets_fund.id:
                impact["toilets"] += project.product_number_reached

            elif project.product_id == scp_fund.id:
                impact["csp"] += project.product_number_reached

            elif project.product_id:
                impact["other"] += project.product_number_reached

        return impact
