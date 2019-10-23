# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
import json

from odoo import http, tools
from odoo.http import request
from ..tools import SmsNotificationAnswer

is_async = not tools.config.get('test_enable')

_logger = logging.getLogger(__name__)


class RestController(http.Controller):

    @http.route('/sms/mnc/', type='http', auth='public', methods=['GET'],
                csrf=False)
    def sms_notification(self, **parameters):
        _logger.info("SMS Request received : {}".format(
            json.dumps(parameters)))

        notification_env = request.env['sms.notification'].sudo()
        (notification_env.with_delay(priority=1) if is_async else
         notification_env).send_sms_answer(parameters)
        return SmsNotificationAnswer([], costs=[]).get_answer()
