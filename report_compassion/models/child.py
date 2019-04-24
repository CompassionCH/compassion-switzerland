# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import timedelta

from odoo import api, models, fields


class CompassionChild(models.Model):
    """ Add fields for retrieving values for communications.
    Send a communication when a major revision is received.
    """
    _inherit = 'compassion.child'

    description_left = fields.Text(compute='_compute_description')
    description_right = fields.Text(compute='_compute_description')
    project_title = fields.Char(compute='_compute_project_title')
    childpack_expiration = fields.Datetime(
        compute='_compute_childpack_expiration')

    @api.multi
    def _compute_description(self):
        lang_map = {
            'fr_CH': 'desc_fr',
            'de_DE': 'desc_de',
            'en_US': 'desc_en',
            'it_IT': 'desc_it',
        }

        for child in self:
            lang = self.env.lang or 'en_US'
            try:
                description = getattr(child, lang_map.get(lang))
            except:
                continue

            child.description_left = description

    def _compute_project_title(self):
        for child in self:
            firstname = child.preferred_name
            suffix_s = 's' if not firstname.endswith('s') else ''
            lang_map = {
                'fr_CH': u"À propos du centre d'accueil",
                'de_DE': u"Über %s Kinderzentrum" % (firstname + suffix_s),
                'en_US': firstname + u"'s Project",
                'it_IT': u'Project',
            }
            lang = self.env.lang or 'en_US'
            child.project_title = lang_map.get(lang)

    def _compute_childpack_expiration(self):
        for child in self:
            hold_expiration = fields.Datetime.from_string(
                child.hold_expiration)
            try:
                child.childpack_expiration = fields.Datetime.to_string(
                    hold_expiration - timedelta(days=1)
                )
            except TypeError:
                child.childpack_expiration = False
