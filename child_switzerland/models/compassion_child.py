##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Coninckx <david@coninckx.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import timedelta

import pyqrcode

from odoo import fields, models


class CompassionChild(models.Model):
    _inherit = "compassion.child"

    description_fr = fields.Html("French description", readonly=True)
    description_de = fields.Html("German description", readonly=True)
    description_it = fields.Html("Italian description", readonly=True)
    description_left = fields.Html(compute="_compute_description")
    description_right = fields.Html(compute="_compute_description")
    project_title = fields.Char(compute="_compute_project_title")
    childpack_expiration = fields.Datetime(compute="_compute_childpack_expiration")
    qr_code_data = fields.Binary(
        compute="_compute_qr_code", help="QR code for sponsoring the child"
    )

    def _compute_description(self):
        lang_map = {
            "fr_CH": "description_fr",
            "de_DE": "description_de",
            "en_US": "description_en",
            "it_IT": "description_it",
        }

        for child in self:
            lang = self.env.lang or "en_US"
            description = getattr(child, lang_map.get(lang), False)
            child.description_left = description
            child.description_right = ""

    def _compute_project_title(self):
        for child in self:
            firstname = child.preferred_name
            suffix_s = "s" if not firstname.endswith("s") else ""
            lang_map = {
                "fr_CH": "À propos du centre de développement de l’enfant",
                "de_DE": f"Über {firstname + suffix_s} Kinderzentrum",
                "en_US": firstname + "'s Project",
                "it_IT": "Project",
            }
            lang = self.env.lang or "en_US"
            child.project_title = lang_map.get(lang)

    def _compute_childpack_expiration(self):
        for child in self:
            hold_expiration = child.hold_expiration
            try:
                child.childpack_expiration = fields.Datetime.to_string(
                    hold_expiration - timedelta(days=1)
                )
            except TypeError:
                child.childpack_expiration = False

    def _compute_qr_code(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.external.url")
        for child in self:
            url = f"{base_url}" f"/sponsor_this_child?source=QR&child_id={child.id}"
            qr = pyqrcode.create(url)
            child.qr_code_data = qr.png_as_base64_str(15, (0, 84, 166))
