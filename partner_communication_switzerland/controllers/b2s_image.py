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
    @http.route("/b2s_image", type="http", auth="public", methods=["GET"])
    # We don't want to rename parameter id because it's used by our sponsors
    # pylint: disable=redefined-builtin
    def handler_b2s_image(self, id=None, disposition=None, file_type=None):
        """
        URL for downloading a correspondence PDF
        (or ZIP when multiple letters are attached).
        Find the associated communication and mark all related letters
        as opened and read.
        :param id: uuid of the correspondence holding the data.
        :param disposition: "inline" to show in browser or None to download.
        :param file_type: can force to use the PDF even though stored as ZIP.
        :return: file data for user
        """
        res = super().handler_b2s_image(id, disposition, file_type)
        correspondence_obj = request.env["correspondence"].sudo()
        correspondence = correspondence_obj.search([("uuid", "=", id)])
        if correspondence.communication_id:
            all_letters = correspondence.communication_id.get_objects()
            all_letters.write({"letter_delivered": True, "email_read": datetime.now()})
        return res
