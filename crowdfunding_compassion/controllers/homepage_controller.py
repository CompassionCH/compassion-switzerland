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
            ]
        }

        return request.render("crowdfunding_compassion.homepage", context)

    def _compute_projects_impact(self, year, **kwargs):
        projects = request.env['crowdfunding.project'].search([
            ('deadline', '>=', datetime(year, 1, 1)),
            ('deadline', '<=', datetime(year, 12, 31)),
        ])

        impact = {
            'sponsorship': 0,
            'toilets': 0,
            'mothers_and_baby': 0,
            'other': 0,
        }

        for project in projects:
            impact['sponsorships'] += project.number_sponsorships_reached

            # TODO: Add fund id
            if project.product_id == '':
                impact['toilets'] += project.product_number_reached

            # TODO: Add fund id
            elif project.product_id == '':
                impact['toilets'] += project.product_number_reached

            elif project.product_id:
                impact['other'] += project.product_number_reached
        
        return impact