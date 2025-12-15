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
    ENGAGEMENT_TYPES_ORDER = [
        "Translation",
        "Events",
        "Sport",
        "Prayer",
        "Church presentation",
        "Together",
    ]

    @http.route(
        "/my2/volunteering", type="http", auth="user", website=True, sitemap=False
    )
    def my2_render_volunteering_dashboard_page(self, **kwargs):
        """
        Renders the voluntering dashboard page
        return: An HTTP response containing a rendered
                template with the volunteering content.
        """
        partner = request.env.user.partner_id

        prayer_engagement = request.env["advocate.engagement"].search(
            [("name", "=", "Prayer")], limit=1
        )

        is_prayer_subscribed = (
            prayer_engagement and prayer_engagement in partner.engagement_ids
        )

        engagement_types_sorted = self._get_sorted_engagement_types()

        return request.render(
            "my_compassion_switzerland.my2_volunteering",
            {
                "partner": partner,
                "is_prayer_subscribed": is_prayer_subscribed,
                "engagement_types": engagement_types_sorted,
            },
        )

    @http.route(
        "/subscription/prayer", type="http", auth="user", website=True, sitemap=False
    )
    def my2_update_prayer_subscription(self, **kwargs):
        """
        Marks the partner as interested for volunteering and adds/removes
        the 'Prayer' engagement.Then renders the volunteering dashboard page.
        """
        partner = request.env.user.partner_id

        prayer_engagement = request.env["advocate.engagement"].search(
            [("name", "=", "Prayer")], limit=1
        )

        is_prayer_subscribed = False
        if prayer_engagement:
            if prayer_engagement in partner.engagement_ids:
                # Remove subscription
                partner.write({"engagement_ids": [(3, prayer_engagement.id)]})
            else:
                if not partner.advocate_details_id:
                    # If the partner does not have advocate details, create it
                    partner.advocate_details_id = request.env[
                        "advocate.details"
                    ].create(
                        {
                            "partner_id": partner.id,
                        }
                    )
                # Add subscription
                partner.write({"engagement_ids": [(4, prayer_engagement.id)]})
                is_prayer_subscribed = True

        engagement_types = request.env["advocate.engagement"].search(
            [("activate_for_my_compassion", "=", True)]
        )

        return request.render(
            "my_compassion_switzerland.my2_volunteering",
            {
                "partner": partner,
                "is_prayer_subscribed": is_prayer_subscribed,
                "engagement_types": engagement_types,
            },
        )

    @http.route(
        "/my2/volunteering/register",
        type="json",
        auth="user",
        website=True,
        sitemap=False,
    )
    def my2_volunteering_register(self, **kwargs):
        data = kwargs.get("data", {})
        required_fields = ["title", "firstname", "lastname", "email", "phone_number"]
        if not all(data.get(field) for field in required_fields):
            return {"success": False, "error": "Missing required fields"}

        lang = (data.get("lang") or "").lower()
        lang_code = lang.split("_")[0] if "_" in lang else lang

        recipients = {
            "fr": "site_fr_participate@compassion.ch",
            "it": "site_it_participate@compassion.ch",
            "de": "site_de_participate@compassion.ch",
        }
        email_to = recipients.get(lang_code, "site_de_participate@compassion.ch")

        # Send the mail template with context data
        template = (
            request.env["mail.template"]
            .sudo()
            .search([("name", "=", "Volunteer Registration")], limit=1)
        )
        if template:
            template.with_context(
                email_to=email_to,
                lang=lang,
                title=data.get("title"),
                firstname=data.get("firstname"),
                lastname=data.get("lastname"),
                phone_number=data.get("phone_number"),
                email=data.get("email"),
                church=data.get("church"),
                volunteer_roles=data.get("volunteer_roles"),
                comments=data.get("comments"),
            ).send_mail(
                request.env.user.partner_id.id,
                email_values={"email_to": email_to},
                force_send=True,
            )
        else:
            # Log an error if the template is not found
            request.env["ir.logging"].create(
                {
                    "name": "MyCompassionVolunteeringController",
                    "type": "server",
                    "dbname": request.env.cr.dbname,
                    "level": "error",
                    "message": "Mail template for Volunteer Registration not found.",
                    "path": (
                        "/my_compassion_switzerland/controllers/my2_volunteering.py"
                    ),
                    "func": "my2_volunteering_register",
                }
            )
            return {"success": False}

        return {"success": True}

    def _get_sorted_engagement_types(self):
        """
        Retrieves and sorts the activated commitment types. Sorting is based on
        COMMITMENT_TYPES_ORDER (based on oliviers' feedback).
        """
        all_engagement_types = request.env["advocate.engagement"].search(
            [("activate_for_my_compassion", "=", True)]
        )

        order_map = {
            name: index for index, name in enumerate(self.ENGAGEMENT_TYPES_ORDER)
        }
        default_sort_value = len(self.ENGAGEMENT_TYPES_ORDER)

        return sorted(
            all_engagement_types,
            key=lambda engagement: order_map.get(engagement.name, default_sort_value),
        )