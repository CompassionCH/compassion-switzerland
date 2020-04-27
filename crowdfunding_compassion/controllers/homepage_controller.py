from datetime import datetime

from odoo.http import request, route, Controller


class HomepageController(Controller):
    @route("/homepage", auth="public", website=True)
    def homepage(self, **kwargs):
        project_obj = request.env['crowdfunding.project']
        context = {
            "funds": request.env['product.product'].sudo().search([
                ('activate_for_crowdfunding', '=', True)
            ]),
            "impact": self._compute_projects_impact(datetime.now().year),
            "project_list": project_obj._get_active_projects_list(),
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
        impact = {
            "sponsorship": {
                "number": 0,
                "image": None
            },
            "toilets": {
                "number": 0,
                "image": None
            },
            "csp": {
                "number": 0,
                "image": None
            },
            "other": {
                "number": 0,
                "image": None
            }
        }

        toilets_fund = request.env.ref(
            "sponsorship_switzerland.product_template_fund_toilets"
        )
        csp_fund = request.env.ref("sponsorship_switzerland.product_template_fund_csp")

        for project in projects:
            impact["sponsorship"]["number"] += project.number_sponsorships_reached

            if project.product_id.id == toilets_fund.id:
                impact["toilets"]["number"] += project.product_number_reached

            elif project.product_id.id == csp_fund.id:
                impact["csp"]["number"] += project.product_number_reached

            elif project.product_id:
                impact["other"]["number"] += project.product_number_reached

        # TODO check if product_variant_id correct
        impact['sponsorship']["image"] = toilets_fund.fund_image      # TODO change
        impact['toilets']["image"] = toilets_fund.fund_image
        impact['csp']["image"] = csp_fund.fund_image
        impact['other']["image"] = csp_fund.fund_image                # TODO change

        return impact
