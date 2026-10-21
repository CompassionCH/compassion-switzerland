from odoo import api, models


class EventFlight(models.Model):
    _inherit = "event.flight"

    @api.model_create_multi
    def create(self, vals_list):
        flights = super().create(vals_list)
        # The outbound and the return flights each have their task.
        tasks = {
            "outbound": self.env.ref("website_switzerland.task_flight_details"),
            "return": self.env.ref("website_switzerland.task_return_flight"),
        }
        for flight in flights:
            task = tasks.get(flight.flight_type)
            flight.registration_id.task_ids.filtered(
                lambda t, task=task: t.task_id == task
            ).write({"done": True})
        return flights
