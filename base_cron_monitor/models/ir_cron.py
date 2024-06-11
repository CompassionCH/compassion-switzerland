# Copyright 2024 Emmanuel Cino
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class IrCron(models.Model):
    _inherit = "ir.cron"

    @api.model
    def _handle_callback_exception(
        self, cron_name, server_action_id, job_id, job_exception
    ):
        super()._handle_callback_exception(
            cron_name, server_action_id, job_id, job_exception
        )
        my_cron = self.browse(job_id).sudo()
        my_cron.with_delay().write({"last_exception": str(job_exception)})

    def clear_exception(self):
        return self.write({"last_exception": False})
