##############################################################################
#
#    Copyright (C) 2025 Compassion CH (http://www.compassion.ch)
#    @author: Daniel Palumbo <daniel.palumbo@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import _, http
from odoo.http import request


class MyCompassionVolunteeringController(http.Controller):
    @http.route(
        "/my2/volunteering", type="http", auth="user", website=True, sitemap=False
    )
    def my2_render_volunteering_dashboard_page(self, **kwargs):
        """
        Renders the volunteering dashboard page
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

        engagement_types = request.env["advocate.engagement"].search(
            [("activate_for_my_compassion", "=", True)],
            order="my_compassion_external_link desc, sequence",
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
                    partner.advocate_details_id = (
                        request.env["advocate.details"]
                        .sudo()
                        .create(
                            {
                                "partner_id": partner.id,
                            }
                        )
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

        if not data.get("volunteer_roles"):
            return {"success": False, "error": _("Missing required volunteer roles")}

        partner = request.env.user.partner_id

        lang_code = (partner.lang or "en").split("_")[0]

        # Fetch the appropriate recipient email based on the language as a dictionary
        recipients = request.env[
            "res.config.settings"
        ].get_advocate_engagement_recipients()
        email_to = (
            recipients.get(lang_code) or recipients["default"] or "info@compassion.ch"
        )

        # Send the mail template with context data
        template = (
            request.env["mail.template"]
            .sudo()
            .search([("name", "=", "Volunteer Registration")], limit=1)
        )
        if template:
            template.with_context(
                email_to=email_to,
                lang=partner.lang,
                title=partner.title,
                firstname=partner.firstname,
                lastname=partner.lastname,
                phone_number=partner.phone_sanitized,
                email=partner.email,
                church=partner.church_id and partner.church_id.name,
                volunteer_roles=data.get("volunteer_roles"),
                comments=data.get("comments"),
            ).send_mail(
                partner.id,
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
