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

from odoo import http
from odoo.http import request


class RestController(http.Controller):

    @http.route('/sms/939/', type='http', auth='public', methods=['GET'],
                csrf=False)
    def sms_notification(self, **parameters):
        sms = request.env['sms.notification'].sudo().create({
            'instance': parameters.get('instance'),
            'sender': parameters.get('sender'),
            'operator': parameters.get('operator'),
            'service': parameters.get('service'),
            'language': parameters.get('language'),
            'date': parameters.get('receptionDate'),
            'uuid': parameters.get('requestUid'),
            'text': parameters.get('text'),
        })
        return sms.run_service()
