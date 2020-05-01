from datetime import datetime

from odoo.http import request, route, Controller


class HomepageController(Controller):
    @route("/homepage", auth="public", website=True)
    def homepage(self, **kwargs):
        project_obj = request.env["crowdfunding.project"]
        context = {
            "funds": request.env["product.product"]
            .sudo()
            .search([("activate_for_crowdfunding", "=", True)]),
            "impact": self._compute_projects_impact(datetime.now().year)[0],
            "fund_names": self._compute_projects_impact(datetime.now().year)[1],
            "project_list": project_obj.sudo().get_active_projects_list(),
        }

        return request.render("crowdfunding_compassion.homepage_template", context)

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
        active_funds = (
            request.env["product.product"]
            .sudo()
            .search([("activate_for_crowdfunding", "=", True)])
        )
        impact = {
            "sponsorship": {
                "number": 0,
                "image": None,
                "impact_text": "sponsored children",
            },
            "other": {
                "number": 0,
                "image": None,
                "impact_text": "donated to various funds",
            },
        }
        fund_name_list = []
        for fund in active_funds:
            fund_name_list.append(fund.name)
            impact.update(
                {
                    fund.name: {
                        "number": 0,
                        "image": fund.image_medium,
                        "impact_text": fund.crowdfunding_impact_text_passive,
                    }
                }
            )

        for project in projects:
            impact["sponsorship"]["number"] += project.number_sponsorships_reached

            if project.product_id.name in fund_name_list:
                impact[project.product_id.name][
                    "number"
                ] += project.product_number_reached

            elif project.product_id:
                impact["other"]["number"] += project.product_number_reached

        impact["sponsorship"][
            "image"
        ] = "crowdfunding_compassion/static/src/img/defaut_fund_icon.png"
        impact["other"][
            "image"
        ] = "crowdfunding_compassion/static/src/img/defaut_fund_icon.png"

        return impact, fund_name_list
