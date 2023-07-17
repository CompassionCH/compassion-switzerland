##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields


class CompassionProject(models.Model):
    """Add short description for child dossiers."""

    _inherit = "compassion.project"

    description = fields.Text(compute="_compute_description")
    description_left = fields.Text(compute="_compute_description")
    description_right = fields.Text(compute="_compute_description")

    @api.multi
    def _compute_description(self):
        lang_map = {
            "fr_CH": "description_fr",
            "de_DE": "description_de",
            "en_US": "description_en",
            "it_IT": "description_it",
        }

        for project in self:
            lang = self.env.lang or "en_US"
            description = getattr(project, lang_map.get(lang), "")
            project.description_right = description
