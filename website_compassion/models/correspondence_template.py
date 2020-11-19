##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    @author: Théo Nikles <theo.nikles@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields


class CorrespondenceTemplate(models.Model):
    _inherit = "correspondence.template"

    website_published = fields.Boolean()
    template_image_url = fields.Char(compute="_compute_template_image_url")

    def _compute_template_image_url(self):
        web_base_url = (self.env["ir.config_parameter"].sudo()
                        .get_param("web.external.url"))
        for template in self:
            template.template_image_url =\
                f"{web_base_url}/web/image/{template._name}/" \
                f"{template.id}/template_image"
