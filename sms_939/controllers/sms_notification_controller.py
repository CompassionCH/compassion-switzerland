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

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class RestController(http.Controller):
    @http.route(
        "/sms/delivery/", type="http", auth="public", methods=["GET"], csrf=False
    )
    def sms_delivery_status(self, **parameters):
        # ?requestUid=xml9677321&sentMessageUid=sms824762&receiver=%2B33612345678
        # &operator=orange&service=ULTIMATE&status=delivered

        sms = (
            request.env["sms.sms"]
            .sudo()
            .search(
                [
                    ("number", "=", parameters.get("receiver")),
                    ("request_uid", "=", parameters.get("requestUid")),
                ]
            )
        )
        mm_id = (
            request.env["mail.message"]
            .sudo()
            .search(
                [
                    ("message_type", "=", "sms"),
                    ("request_uid", "=", parameters.get("requestUid")),
                ]
            )
        )
        if mm_id:
            _logger.info(f"SMS Status received : {json.dumps(parameters)}")
            notification = mm_id.notification_ids
            if parameters.get("status") in ("sent", "delivered"):
                notification.unlink()
                request.env["mail.notification"].sudo().create(
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
