from odoo.http import Controller, request, route

from odoo.addons.http_routing.models.ir_http import slug


class MyEventsController(Controller):
    @route("/my/events/travel_contract", auth="user", website=True, sitemap=False)
    def travel_contract(self, **kwargs):
        contract_task = request.env.ref("website_switzerland.task_sign_travel")
        if kwargs.get("accept"):
            partner = request.env.user.partner_id
            travel_task = (
                request.env["event.registration.task.rel"]
                .sudo()
                .search(
                    [
                        ("registration_id.partner_id", "=", partner.id),
                        ("task_id", "=", contract_task.sudo().id),
                    ]
                )
            )
            travel_task.write({"done": True})
        return request.redirect(
            f"/my/events/{slug(travel_task.registration_id) if travel_task else ''}"
        )
