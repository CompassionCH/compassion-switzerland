import time
import traceback
from datetime import timedelta

from odoo import SUPERUSER_ID, api, models, registry


class ServerAction(models.Model):
    _inherit = "ir.actions.server"

    def run(self):
        exception = False
        res = False
        e = None
        start_time = time.time()
        try:
            res = super().run()
        except Exception as ex:
            exception = traceback.format_exc()
            e = ex
        end_time = time.time()
        execution_time = timedelta(seconds=end_time - start_time)
        with api.Environment.manage():
            with registry(self.env.cr.dbname).cursor() as new_cr:
                # Create a new environment with new cursor database
                new_env = api.Environment(new_cr, SUPERUSER_ID, self.env.context)
                self.with_env(new_env).env["server.action.monitor"].create(
                    {
                        "server_action_id": self.id,
                        "user_id": self.env.user.id,
                        "execution_time": str(execution_time),
                        "exception": exception,
                    }
                )
        if exception and e:
            raise e
        return res
