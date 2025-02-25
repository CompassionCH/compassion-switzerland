# Copyright 2024 Emmanuel Cino
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import time
import traceback
from datetime import timedelta

from odoo import SUPERUSER_ID, fields, models


class BaseAutomation(models.Model):
    _inherit = "base.automation"

    def _process(self, records, domain_post=None):
        start_time = time.time()
        try:
            super()._process(records, domain_post)
        except Exception:
            self.with_user(SUPERUSER_ID).with_delay().write(
                {
                    "last_exception": traceback.format_exc(),
                    "last_exception_time": fields.Datetime.now(),
                }
            )
        end_time = time.time()
        execution_time = timedelta(seconds=end_time - start_time)
        self.sudo().write(
            {
                "last_execution_time": str(execution_time),
            }
        )

    def clear_exception(self):
        return self.write(
            {
                "last_exception": False,
                "last_exception_time": False,
            }
        )
