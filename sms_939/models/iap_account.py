# Copyright 2024 Compassion (https://www.compassion.ch).
# @author David Wulliamoz <dwulliamoz@compassion.ch>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class IapAccount(models.Model):
    _inherit = "iap.account"

    provider = fields.Selection(
        selection_add=[
            ("sms_mnc_http", "SMS MNC http"),
            ("sms_mnc_shortnum", "SMS Short MNC"),
        ],
        ondelete={"sms_mnc_http": "cascade", "sms_mnc_shortnum": "cascade"},
    )
    server_939 = fields.Char("Provider server", required=True)
    port_939 = fields.Integer("Server port", required=True)
    endpoint_939 = fields.Char("Endpoint", required=True)
    username_939 = fields.Char("Username for login", required=True)
    password_939 = fields.Char("Password for login", required=True)

    def _get_service_from_provider(self):
        if self.provider == "sms_mnc_http":
            return "sms"
        if self.provider == "sms_mnc_shortnum":
            return "sms_short"

    @property
    def _server_env_fields(self):
        res = super()._server_env_fields
        res.update(
            {
                "server_939": {},
                "port_939": {},
                "endpoint_939": {},
                "username_939": {},
                "password_939": {},
            }
        )
        return res
