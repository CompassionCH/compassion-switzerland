from odoo.http import Controller, request, route


class MyEventsController(Controller):
    @route("/my/events/travel_contract", auth="user", website=True, sitemap=False)
    def travel_contract(self, registration_id=None, **kwargs):
        contract_task = request.env.ref("website_switzerland.task_sign_travel")
        # Only the trip the contract was read for, not the other registrations
        # of the participant.
        travel_task = (
            request.env["event.registration.task.rel"]
            .sudo()
            .search(
                [
                    (
                        "registration_id",
                        "=",
                        int(registration_id) if str(registration_id).isdigit() else 0,
                    ),
                    ("registration_id.partner_id", "=", request.env.user.partner_id.id),
                    ("task_id", "=", contract_task.sudo().id),
                ]
            )
        )
        if kwargs.get("accept"):
            travel_task.write({"done": True})
        slug = request.env["ir.http"]._slug
        return request.redirect(
            f"/my/events/{slug(travel_task.registration_id) if travel_task else ''}"
        )
