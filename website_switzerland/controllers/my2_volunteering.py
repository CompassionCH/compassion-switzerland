##############################################################################
#
#    Copyright (C) 2025 Compassion CH (http://www.compassion.ch)
#    @author: Daniel Palumbo <daniel.palumbo@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import http
from odoo.http import request


class MyCompassionVolunteeringController(http.Controller):
    @http.route(
        "/my2/volunteering/", type="http", auth="user", website=True, sitemap=False
    )
    def my2_render_volunteering_dashboard_page(self, **kwargs):

        """
        Renders the voluntering dashboard page
        return: An HTTP response containing a rendered template with the volunteering content.
        """
        # Search for all advocate.engagement records with activate_for_my_compassion = True
        engagement_types = request.env["advocate.engagement"].search([
            ("activate_for_my_compassion", "=", True)
        ])

        return request.render(
            "website_switzerland.my2_volunteering",
            {
                "engagement_types": engagement_types
            }
        )