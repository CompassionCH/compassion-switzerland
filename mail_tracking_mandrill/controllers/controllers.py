# Copyright 2021 Compassion CH (http://www.compassion.ch)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
import hmac
import json
import logging
from hashlib import sha1

from odoo import http
from odoo.http import request
from odoo.tools import config

from odoo.addons.mail_tracking.controllers.main import MailTrackingController

_logger = logging.getLogger(__name__)


class MandrillTrackingController(MailTrackingController):
    def _mandrill_validation(self, db, **kwargs):
        """
        Validate webhook request comes from mandrill and not from potentially
        malicious third party.

        `mandrill_webhook_key` must be specified in configuration file to allow
        the validation process to work.
        Without the webhook key any request will be validate.

        Validation process is described in mandrill documentation.
        "https://mandrill.zendesk.com/hc/en-us/articles/205583257-Authenticating-webhook-requests"
        :return:
        """
        headers = request.httprequest.headers
        webhook_key = config.get("mandrill_webhook_key", False)
        signature = headers.get("X-Mandrill-Signature", False)
        if not webhook_key:
            _logger.info(
                "No Mandrill validation key configured. "
                "Please add 'mandrill_webhook_key' to [options] "
                "section in odoo configuration file to enable "
                "Mandrill authentication webhoook requests. "
                "More info at: "
                "https://mandrill.zendesk.com/hc/en-us/articles/"
                "205583257-Authenticating-webhook-requests"
            )
            return True

        if not signature:
            return False

        url = request.httprequest.url_root.rstrip("/") + f"/mail/tracking/mandrill/{db}"

        data = url
        kw_keys = list(kwargs.keys())
        if kw_keys:
            kw_keys.sort()
            for kw_key in kw_keys:
                data += kw_key + kwargs.get(kw_key)

        webhook_key = webhook_key.encode()
        hash_text = base64.b64encode(
            hmac.new(webhook_key, msg=data.encode("utf-8"), digestmod=sha1).digest()
        ).decode()
        if hash_text == signature:
            return True
        _logger.info("HASH[%s] != SIGNATURE[%s]" % (hash_text, signature))
        return True

    @http.route(
        "/mail/tracking/mandrill/<string:db>", type="http", auth="none", csrf=False
    )
    def mail_tracking_mandrill(self, db, **kwargs):
        """
        Route for mandrill webhook
        :param db: The db to connect to
        :param kwargs: dictionary containing events information
        :return:
        """
        if not self._mandrill_validation(db, **kwargs):
            _logger.info("Validation error, ignoring this request")
            return "NO_AUTH"
        try:
            kwargs["mandrill_events"] = json.loads(kwargs.get("mandrill_events", "[]"))
            self.mail_tracking_event(db, **kwargs)
            return "OK"
        except Exception as e:
            _logger.error(e.args[0] or e.message, exc_info=True)
            return "ERROR"
