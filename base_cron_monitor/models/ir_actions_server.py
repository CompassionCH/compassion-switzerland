import time
from datetime import timedelta

from odoo import fields, models


class ServerAction(models.Model):
    _inherit = "ir.actions.server"

    last_execution_time = fields.Char(
        string="Last Execution Time",
        readonly=True,
        help="Last execution time of the job.",
    )
    last_exception = fields.Text()

    def run(self):
        start_time = time.time()
        res = super().run()
        end_time = time.time()
        execution_time = timedelta(seconds=end_time - start_time)
        self.sudo().write({"last_execution_time": str(execution_time)})
        return res
