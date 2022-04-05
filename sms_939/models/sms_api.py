import base64
import http.client
import urllib.request
import urllib.parse
import urllib.error
import logging

from bs4 import BeautifulSoup

from odoo import api, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SmsApi(models.AbstractModel):
    _inherit = "sms.api"

    @api.model
    def _send_sms(self, numbers, message):
        """ Send sms using MNC 939 provider
        """
        odoo_provider = self.env.ref("sms_939.sms_odoo")
        sms_provider = self.env.context.get("sms_provider", odoo_provider)
        if sms_provider != odoo_provider:
            # Use MNC API to send SMS
            headers = {}
            auth = base64.b64encode(
                f"{sms_provider.username_939}:{sms_provider.password_939}".encode()
            )
            headers["Authorization"] = "Basic " + auth.decode()
            server_config = {
                "server": sms_provider.server_939,
                "port": sms_provider.port_939,
                "endpoint": sms_provider.endpoint_939,
            }
            for mobile in numbers:
                request = [
                    ("receiver", mobile.replace(" ", "")),
                    ("service", "compassion"),
                    ("maximumSMSAmount", 4),
                    ("cost", 0),
                    ("text", message),
                ]
                return self._smsbox_send(request, headers, server_config)
        else:
            return super()._send_sms(numbers, message)

    def _smsbox_send(self, request, headers, config):
        server = config["server"]
        port = config["port"]
        endpoint = config["endpoint"]
        request_server = http.client.HTTPConnection(server, port, timeout=10)
        url = endpoint + "?" + urllib.parse.urlencode(request)
        _logger.debug(f"Sending SMS message: {url}")
        request_server.request("GET", url, headers=headers)
        response = request_server.getresponse()
        result = response.read()
        _logger.debug(f"SMS response status: {response.status}")
        _logger.debug(result)
        if response.code != 200 or "error" in str(result):
            soup = BeautifulSoup(result, "html")
            raise UserError(_("SMS was not delivered: \n %s")
                            % soup.smsboxxmlreply.prettify())
        return True
