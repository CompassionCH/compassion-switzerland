# Copyright 2021 Compassion CH (http://www.compassion.ch)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import json

from odoo import models


class IrMailServer(models.Model):
    _inherit = "ir.mail_server"

    def _tracking_headers_add(self, tracking_email_id, headers):
        """
        Append tracking_email_id to any outgoing mail. Webhook request can then use
        those information
        :param tracking_email_id: id of the tracking_email object in odoo
        :return: headers with added tracking metadata
        """
        headers = super(IrMailServer, self)._tracking_headers_add(
            tracking_email_id, headers
        )
        headers = headers or {}
        metadata = {
            "tracking_email_id": tracking_email_id,
        }
        headers["X-MC-Metadata"] = json.dumps(metadata)
        return headers
