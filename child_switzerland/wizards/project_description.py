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

    SWISS_DESCRIPTIONS = {
        "de_DE": "desc_de",
        "fr_CH": "desc_fr",
        "it_IT": "desc_it",
    }

    @api.model
    def _supported_languages(self):
        """
        Inherit to add more languages to have translations of
        descriptions.
        {lang: description_field}
        """
        res = super()._supported_languages()
        res.update(self.SWISS_DESCRIPTIONS)
        return res
