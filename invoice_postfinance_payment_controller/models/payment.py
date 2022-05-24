##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, api, _
from odoo.http import request

class CompassionPayment(models.Model):

    _inherit = "payment.acquirer"

    @api.multi
    def get_base_url(self):
        return request.httprequest.host_url.strip("/")
