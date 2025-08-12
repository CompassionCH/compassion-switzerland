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
        "/my2/volunteering", type="http", auth="user", website=True, sitemap=False
    )
    def my2_render_volunteering_dashboard_page(self, **kwargs):
        """
        Renders the voluntering dashboard page
        return: An HTTP response containing a rendered template with the volunteering content.
        """
        partner = request.env.user.partner_id

        prayer_engagement = request.env["advocate.engagement"].search([
            ("name", "=", "Prayer")
        ], limit=1)

        is_prayer_subscribed = prayer_engagement and prayer_engagement in partner.engagement_ids

        # Search for all advocate.engagement records with activate_for_my_compassion = True
        engagement_types = request.env["advocate.engagement"].search([
            ("activate_for_my_compassion", "=", True)
        ])

        return request.render(
            "website_switzerland.my2_volunteering",
            {
                "partner": partner,
                "is_prayer_subscribed": is_prayer_subscribed,
                "engagement_types": engagement_types
            }
        )

    @http.route(
        "/subscription/prayer", type="http", auth="user", website=True, sitemap=False
    )
    def my2_update_prayer_subscription(self, **kwargs):
        """
        Marks the partner as interested for volunteering and adds/removes the 'Prayer' engagement.
        Then renders the volunteering dashboard page.
        """
        partner = request.env.user.partner_id  # sudo to bypass portal restrictions

        prayer_engagement = request.env["advocate.engagement"].search([
            ("name", "=", "Prayer")
        ], limit=1)

        is_prayer_subscribed = False
        if prayer_engagement:
            if prayer_engagement in partner.engagement_ids:
                # Remove subscription
                partner.write({
                    "engagement_ids": [(3, prayer_engagement.id)]
                })
            else:
                if not partner.advocate_details_id:
                    # If the partner does not have advocate details, create it
                    partner.advocate_details_id = request.env["advocate.details"].create({
                        "partner_id": partner.id,
                    })
                # Add subscription
                partner.write({
                    "engagement_ids": [(4, prayer_engagement.id)]
                })
                is_prayer_subscribed = True

        engagement_types = request.env["advocate.engagement"].sudo().search([
            ("activate_for_my_compassion", "=", True)
        ])

        return request.render(
            "website_switzerland.my2_volunteering",
            {
                "partner": partner,
                "is_prayer_subscribed": is_prayer_subscribed,
                "engagement_types": engagement_types
            }
        )

