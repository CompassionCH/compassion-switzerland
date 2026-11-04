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

    def unlink(self):
        # A direction left without any flight has its task to do again.
        directions = {(flight.registration_id, flight.flight_type) for flight in self}
        res = super().unlink()
        tasks = {
            "outbound": self.env.ref("website_switzerland.task_flight_details"),
            "return": self.env.ref("website_switzerland.task_return_flight"),
        }
        for registration, flight_type in directions:
            task = tasks.get(flight_type)
            if task and flight_type not in registration.flight_ids.mapped(
                "flight_type"
            ):
                registration.task_ids.filtered(
                    lambda t, task=task: t.task_id == task
                ).write({"done": False})
        return res
