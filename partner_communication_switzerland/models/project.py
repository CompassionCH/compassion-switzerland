# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from pyquery import PyQuery
from openerp import api, models, fields


class CompassionProject(models.Model):
    """ Add short description for child dossiers.
    """
    _inherit = 'compassion.project'

    short_desc = fields.Text(compute='_compute_description')
    description = fields.Text(compute='_compute_description')

    @api.multi
    def _compute_description(self):
        lang_map = {
            'fr_CH': 'description_fr',
            'de_DE': 'description_de',
            'en_US': 'description_en',
            'it_IT': 'description_it',
        }
        for project in self:
            project.description = getattr(project, lang_map.get(self.env.lang))
            desc = PyQuery(
                getattr(project, lang_map.get(self.env.lang))
            )
            desc('#spiritual_activities').prev().remove()
            desc('#spiritual_activities').remove()
            desc('#spiritual_activities').remove()
            desc('#physical_activities').remove()
            desc('#cognitive_activities').remove()
            desc('#socio_activities').remove()
            project.short_desc = desc.outer_html()
