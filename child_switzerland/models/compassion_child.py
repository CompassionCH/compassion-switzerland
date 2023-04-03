##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Coninckx <david@coninckx.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import pyqrcode

from odoo import models, fields


class CompassionChild(models.Model):
    _inherit = "compassion.child"

    desc_fr = fields.Html("French description", readonly=True)
    desc_de = fields.Html("German description", readonly=True)
    desc_it = fields.Html("Italian description", readonly=True)
    qr_code_data = fields.Binary(compute="_compute_qr_code",
                                 help="QR code for sponsoring the child")

    def _compute_qr_code(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.external.url")
        for child in self:
            url = f"{base_url}/sponsor_this_child?source=QR&child_id={child.id}"
            qr = pyqrcode.create(url)
            child.qr_code_data = qr.png_as_base64_str(15, (0, 84, 166))