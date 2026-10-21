from odoo import api, models


class EventFlight(models.Model):
    _inherit = "event.flight"

    @api.model_create_multi
    def create(self, vals_list):
        flights = super().create(vals_list)
        task_flight = self.env.ref("website_switzerland.task_flight_details")
        for registration in flights.registration_id:
            # The outbound and the return flights are both needed.
            if len(registration.flight_ids) == 2:
                registration.task_ids.filtered(
                    lambda t: t.task_id == task_flight
                ).write({"done": True})
        return flights
