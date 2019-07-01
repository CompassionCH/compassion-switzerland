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
from datetime import datetime

from odoo import http
from odoo.http import request
from odoo.addons.sbc_compassion.controllers.b2s_image import RestController

_logger = logging.getLogger(__name__)


class B2sControllerSwitzerland(RestController):

    @http.route('/b2s_image', type='http', auth='public', methods=['GET'])
    def handler_b2s_image(self, id=None):
        """
        URL for downloading a correspondence PDF
        (or ZIP when multiple letters are attached).
        Find the associated communication and mark all related letters
        as opened and read.
        :param image_id: uuid of the correspondence holding the data.
        :return: file data for user
        """
        res = super(B2sControllerSwitzerland, self).handler_b2s_image(id)
        correspondence_obj = request.env['correspondence'].sudo()
        correspondence = correspondence_obj.search([('uuid', '=', id)])
        if correspondence.communication_id:
            all_letters = correspondence.communication_id.get_objects()
            all_letters.write({
                'letter_delivered': True,
                'email_read': datetime.now()
            })
        return res
