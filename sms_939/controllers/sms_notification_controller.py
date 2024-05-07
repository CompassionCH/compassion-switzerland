##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import json
import logging
from datetime import datetime

from odoo import http, tools
from odoo.http import request

from ..tools import SmsNotificationAnswer

is_async = not tools.config.get("test_enable")

_logger = logging.getLogger(__name__)


class RestController(http.Controller):
    @http.route("/sms/mnc/", type="http", auth="public", methods=["GET"], csrf=False)
    def sms_notification(self, **parameters):
        # ...base url...
        # ?instance=pro&sender=%2B244342126&operator=orange&service=ULTIMATE&language=fr
        # &command=FORWARD&receptionDate=2014-04-12+12%3A00%3A00.000
        # &requestUid=sms21342314&text=COMPASSION
        _logger.info(f"SMS Request received : {json.dumps(parameters)}")

        notification_env = request.env["sms.notification"].sudo()
        (
            notification_env.with_delay(priority=1) if is_async else notification_env
        ).send_sms_answer(parameters)
        return SmsNotificationAnswer([], costs=[]).get_answer()

    @http.route(
        "/sms/delivery/", type="http", auth="public", methods=["GET"], csrf=False
    )
    def sms_delivery_status(self, **parameters):
        # ?requestUid=xml9677321&sentMessageUid=sms824762&receiver=%2B33612345678
        # &operator=orange&service=ULTIMATE&status=delivered

        sms = request.env["sms.sms"].search(
            [
                ("number", "=", parameters.get("receiver")),
                ("request_uid", "=", parameters.get("requestUid")),
            ]
        )
        mm_id = request.env["mail.message"].search(
            [
                ("message_type", "=", "sms"),
                ("request_uid", "=", parameters.get("requestUid")),
            ]
        )
        if mm_id:
            _logger.info(f"SMS Status received : {json.dumps(parameters)}")
            notification = mm_id.notification_ids
            if parameters.get("status") in ("sent", "delivered"):
                notification.unlink()
                request.env["mail.notification"].create(
                    {
                        "notification_type": "sms",
                        "sms_id": False,
                        "sms_number": sms.number,
                        "is_read": True,
                        "read_date": datetime.now(),
                        "res_partner_id": mm_id.res_id,
                        "mail_message_id": mm_id.id,
                        "notification_status": "sent",
                    }
                )
                sms.unlink()
            else:
                notification.failure_reason = parameters.get("status")
        else:
            _logger.info(f"SMS Status received - not found : {json.dumps(parameters)}")
