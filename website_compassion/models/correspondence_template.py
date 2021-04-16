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
    _inherit = ["correspondence.template", "website.published.mixin"]
    _name = "correspondence.template"

    website_published = fields.Boolean()
    template_image_url = fields.Char(compute="_compute_template_image_url")

    def _compute_template_image_url(self):
        for template in self:
            template.template_image_url =\
                f"/web/image/{self._name}/{template.id}/template_image?width=300"
