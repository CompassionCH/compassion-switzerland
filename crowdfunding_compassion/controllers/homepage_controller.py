from odoo.http import request, route, Controller


class ProjectController(Controller):
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
