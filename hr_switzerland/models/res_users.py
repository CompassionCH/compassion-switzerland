##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Stephane Eicher <seicher@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

import requests

from odoo import _, fields, models

_logger = logging.getLogger(__name__)


class ResUser(models.Model):
    _inherit = "res.users"

    connect_agent = fields.Boolean(
        string="Connect the Xivo agent after check_in ", default=True
    )

    def asterisk_connect(self, log=True):
        for user in self.filtered("connect_agent"):
            try:
                aso = self.env["asterisk.server"]
                ast_server, auth, url = aso._get_connect_info("/ari/channels")
                channel = user.asterisk_chan_name
                if user.dial_suffix:
                    channel += "/%s" % user.dial_suffix

                _prefix = "*31" if log else "*32"
                extension = _prefix + user.internal_number

                params = {
                    "endpoint": channel,
                    "extension": extension,
                    "context": ast_server.context,
                    "priority": str(ast_server.extension_priority),
                    "timeout": str(ast_server.wait_time),
                    "callerId": user.callerid,
                }
                res_req = requests.post(url, auth=auth, params=params, timeout=10)
                if res_req.status_code == 200:
                    message = (
                        "Your Xivo agent is now "
                        f"{'connected' if log else 'disconnected'}."
                    )
                    user.notify_info(message)
                else:
                    user.notify_warning(
                        _(
                            "Click to dial with Asterisk failed.\n"
                            "HTTP error code: %s."
                        )
                        % res_req.status_code
                    )
            except Exception as e:
                message = "Impossible to connect your Xivo agent\n"
                message += str(e)
                user.notify_info(message)
