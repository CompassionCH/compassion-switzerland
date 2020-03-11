##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models


class ProjectDescription(models.TransientModel):
    _inherit = "compassion.project.description"

    @api.model
    def _supported_languages(self):
        """
        Inherit to add more languages to have translations of
        descriptions.
        {lang: description_field}
        """
        return {
            "en_US": "description_en",
            "de_DE": "description_de",
            "fr_CH": "description_fr",
            "it_IT": "description_it",
        }
