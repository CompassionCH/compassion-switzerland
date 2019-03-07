# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Christopher Meier <dev@c-meier.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models

LANG_MAPPING = {
    'fr': 'fr_CH',
    'de': 'de_DE',
    'it': 'it_IT'
}

TITLE_MAPPING = {
    'Herr': 'base.res_partner_title_mister',
    'Frau': 'base.res_partner_title_madam',
    'Familie': 'partner_compassion.res_partner_title_family',
}

SPOKEN_LANG_MAPPING = {
    u'französich': 'child_compassion.lang_compassion_french',
    u'deutsch': 'child_switzerland.lang_compassion_german',
    u'italienisch': 'child_switzerland.lang_compassion_italian',
    u'spanisch': 'child_compassion.lang_compassion_spanish',
    u'englisch': 'child_compassion.lang_compassion_english',
    u'portugiesisch': 'child_compassion.lang_compassion_portuguese',
}


class MatchPartnerWP(models.AbstractModel):
    """
    Add functionnalities to format the WP values into values understandable by
    Odoo.
    """
    _name = 'res.partner.match.wp'
    _inherit = 'res.partner.match'

    @api.model
    def match_country(self, wp_country, wp_lang):
        country = self.env['res.country'].with_context(
            lang=wp_lang
        ).search([
            ('name', '=ilike', wp_country),
        ])
        return country

    @api.model
    def match_lang(self, wp_lang):
        return LANG_MAPPING.get(wp_lang)

    @api.model
    def match_title(self, wp_title):
        if wp_title in TITLE_MAPPING:
            return self.env.ref(TITLE_MAPPING.get(wp_title)).id
        else:
            title = self.env['res.partner.title'].with_context(
                lang='en_US'
            ).search([
                ('name', '=ilike', wp_title),
            ])
            return title.id

    @api.model
    def match_spoken_langs(self, wp_spoken_langs):
        spoken_langs = self.env['res.lang.compassion']
        for wp_spoken in wp_spoken_langs:
            spoken_langs += self.env.ref(SPOKEN_LANG_MAPPING[wp_spoken])
        lang_write = [(4, lang.id) for lang in spoken_langs]
        return lang_write
