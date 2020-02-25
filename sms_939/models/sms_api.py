import base64
import http.client
import urllib.request
import urllib.parse
import urllib.error
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class SmsApi(models.AbstractModel):
    _inherit = 'sms.api'

    @api.model
    def _send_sms(self, numbers, message):
        """ Send sms using MNC 939 provider
        """
        odoo_provider = self.env.ref('sms_939.sms_odoo')
        sms_provider = self.env.context.get('sms_provider', odoo_provider)
        if sms_provider != odoo_provider:
            # Use MNC API to send SMS
            headers = {}
            auth = base64.b64encode(
                f'{sms_provider.username_939}:{sms_provider.password_939}'.encode())
            headers['Authorization'] = 'Basic ' + auth.decode()
            server_config = {
                'server': sms_provider.server_939,
                'port': sms_provider.port_939,
                'endpoint': sms_provider.endpoint_939
            }
            for mobile in numbers:
                request = [
                    ('receiver', mobile),
                    ('service', 'compassion'),
                    ('maximumSMSAmount', 3),
                    ('cost', 0),
                    ('text', message)
                ]
                self._smsbox_send(request, headers, server_config)
                return True
        else:
            return super()._send_sms(numbers, message)

    def _smsbox_send(self, request, headers, config):
        server = config['server']
        port = config['port']
        endpoint = config['endpoint']
        request_server = http.client.HTTPConnection(server, port, timeout=10)
        url = endpoint + '?' + urllib.parse.urlencode(request)
        _logger.info(f"Sending SMS message: {url}")
        request_server.request('GET', url, headers=headers)
        response = request_server.getresponse()
        _logger.info(f"SMS response status: {response.status}")
        _logger.debug(response.read())
