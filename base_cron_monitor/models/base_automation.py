# Copyright 2024 Emmanuel Cino
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import time
import traceback
from datetime import timedelta

from odoo import models


class BaseAutomation(models.Model):
    _inherit = "base.automation"

    def _process(self, records, domain_post=None):
        start_time = time.time()
        try:
            super()._process(records, domain_post)
        except Exception:
            self.write({"last_exception": traceback.format_exc()})
        end_time = time.time()
        execution_time = timedelta(seconds=end_time - start_time)
        self.write({"last_execution_time": str(execution_time)})

    def clear_exception(self):
        return self.write({"last_exception": False})
