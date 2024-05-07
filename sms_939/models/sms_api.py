import base64
import http.client
import logging
import urllib.error
import urllib.parse
import urllib.request
from xml.etree import ElementTree

from odoo import _, api, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SmsApi(models.AbstractModel):
    _inherit = "sms.api"

    def _prepare_mnc_http_params(self, account, number, message):
        return {
            "login": account.username_939,
            "password": account.password_939,
            "from": "Compassion",
            "endpoint": account.endpoint_939,
            "server": account.server_939,
            "port": account.port_939,
            "to": number,
            "message": message,
            "noStop": 1,
        }

    def _get_sms_account(self, is_short_sms=False):
        if is_short_sms:
            return self.env["iap.account"].get("sms_short")
        else:
            return self.env["iap.account"].get("sms")

    def _send_sms_with_mnc_http(
        self, number, message, sms_id, is_short_sms=False, test=False
    ):
        # Try to return same error code like odoo
        # list is here: self.IAP_TO_SMS_STATE
        if not number:
            return "wrong_number_format"
        account = self._get_sms_account(is_short_sms)
        params = self._prepare_mnc_http_params(account, number, message)
        headers = {}
        auth = base64.b64encode(f"{params['login']}:{params['password']}".encode())
        headers["Authorization"] = "Basic " + auth.decode()
        server_config = {
            "server": params["server"],
            "port": params["port"],
            "endpoint": params["endpoint"],
        }
        request = [
            ("receiver", number),
            ("service", "compassion"),
            ("maximumSMSAmount", 3),
            ("cost", 0),
            ("text", message),
        ]
        req_uid = (
            self._smsbox_send(request, headers, server_config)
            if not test
            else "xml_req_test"
        )
        s = self.env["sms.sms"].browse(sms_id)
        if req_uid:
            s.request_uid = req_uid
            if not s.mail_message_id:
                mm_id = self.env["mail.message"].search(
                    [("body", "=", s.body), ("res_id", "=", s.partner_id.id)]
                )
                if not mm_id:
                    mm_id = self.env["mail.message"].create(
                        {
                            "body": s.body,
                            "res_id": s.partner_id.id,
                            "model": "res.partner",
                            "message_type": "sms",
                        }
                    )
                mm_id.is_internal = False
                s.mail_message_id = mm_id.id
            s.mail_message_id.request_uid = req_uid
            s.error_detail = "waiting status"
        else:
            s.error_detail = "not sent"
        return "server_error"

    def _is_sent_with_mnc(self):
        return (
            self._get_sms_account().provider == "sms_mnc_http"
            or self._get_sms_account().provider == "sms_mnc_shortnum"
        )

    @api.model
    def _send_sms(self, numbers, message):
        if self._is_sent_with_mnc():
            # This method seem to be deprecated (no odoo code use it)
            # as MNC do not support it we do not support it
            # Note: if you want to implement it be carefull just looping
            # on the list of number is not the right way to do it.
            # If you have an error, you will send and send again the same
            # message
            raise NotImplementedError
        else:
            return super()._send_sms(numbers, message)

    @api.model
    def _send_sms_batch(self, messages, test=False):
        if self._is_sent_with_mnc():
            if len(messages) != 1:
                # we already have inherited the split_batch method on sms.sms
                # so this case should not append
                raise UserError(_("Batch sending is not support with MNC"))
            state = self._send_sms_with_mnc_http(
                messages[0]["number"],
                messages[0]["content"],
                messages[0]["res_id"],
                messages[0]["is_short_sms"],
                True,
            )
            return [{"state": state, "credit": 0, "res_id": messages[0]["res_id"]}]
        else:
            return super()._send_sms_batch(messages)

    def _smsbox_send(self, request, headers, config):
        server = config["server"]
        port = config["port"]
        endpoint = config["endpoint"]
        request_server = http.client.HTTPConnection(server, port, timeout=10)
        url = endpoint + "?" + urllib.parse.urlencode(request)
        _logger.info(f"Sending SMS message: {url}")
        request_server.request("GET", url, headers=headers)
        response = request_server.getresponse()
        xml_response = response.read()
        status = ElementTree.fromstring(xml_response)
        _logger.info(f"SMS response status: {status[1][0].attrib['status']}")
        _logger.debug(xml_response)
        if status[1][0].attrib["status"]:
            return status[2].text
        else:
            return False
