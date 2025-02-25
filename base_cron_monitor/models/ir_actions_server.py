import time
from datetime import timedelta

from odoo import fields, models


class ServerAction(models.Model):
    _inherit = "ir.actions.server"

    last_execution_time = fields.Char(
        string="Last Execution Duration",
        readonly=True,
        help="Last execution duration of the job in seconds.",
    )
    last_exception = fields.Text()
    last_exception_time = fields.Datetime()

    def run(self):
        start_time = time.time()
        res = super().run()
        end_time = time.time()
        execution_time = timedelta(seconds=end_time - start_time)
        self.sudo().write({"last_execution_time": str(execution_time)})
        return res
