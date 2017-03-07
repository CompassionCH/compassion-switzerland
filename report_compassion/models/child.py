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


class CompassionChild(models.Model):
    """ Add fields for retrieving values for communications.
    Send a communication when a major revision is received.
    """
    _inherit = 'compassion.child'

    description = fields.Text(compute='_compute_description')
    project_title = fields.Char(compute='_compute_project_title')
    project_about = fields.Text(compute='_compute_project_about')

    @api.multi
    def _compute_description(self):
        lang_map = {
            'fr_CH': 'desc_fr',
            'de_DE': 'desc_de',
            'en_US': 'desc_en',
            'it_IT': 'desc_it',
        }
        for child in self:
            lang = child.sponsor_id.lang or self.env.lang or 'en_US'
            child.description = getattr(child, lang_map.get(lang))

    def _compute_project_title(self):
        for child in self:
            firstname = child.firstname or ''
            lang_map = {
                'fr_CH': u"À propos du centre d'accueil",
                'de_DE': u"Über %s's Projekt" % firstname,
                'en_US': firstname + u"'s Project",
                'it_IT': u'Project',
            }
            lang = child.sponsor_id.lang or self.env.lang or 'en_US'
            child.project_title = lang_map.get(lang)

    def _compute_project_about(self):
        for child in self:
            lang = child.sponsor_id.lang or self.env.lang or 'en_US'
            lang_map = {
                'fr_CH': 'description_fr',
                'de_DE': 'description_de',
                'en_US': 'description_en',
                'it_IT': 'description_it',
            }
            try:
                project_desc = PyQuery(getattr(
                    child.project_id, lang_map[lang]))
                child.project_about = project_desc('table').outerHtml() or ''
            except:
                child.project_about = ''
