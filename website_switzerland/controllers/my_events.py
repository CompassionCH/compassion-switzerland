from odoo.http import Controller, request, route


class MyEventsController(Controller):
    @route("/my/events/travel_contract", auth="user", website=True, sitemap=False)
    def travel_contract(self, **kwargs):
        contract_task = request.env.ref("website_switzerland.task_sign_travel")
        travel_task = request.env["event.registration.task.rel"].sudo()
        if kwargs.get("accept"):
            partner = request.env.user.partner_id
            travel_task = travel_task.search(
                [
                    ("registration_id.partner_id", "=", partner.id),
                    ("task_id", "=", contract_task.sudo().id),
                ]
            )
            travel_task.write({"done": True})
        slug = request.env["ir.http"]._slug
        return request.redirect(
            f"/my/events/{slug(travel_task.registration_id) if travel_task else ''}"
        )
