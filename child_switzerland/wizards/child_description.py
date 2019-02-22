# -*- coding: utf-8 -*-
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

from odoo.addons.child_compassion.wizards.child_description import \
    SINGULAR, NOMINATIVE, ChildDescription


ChildDescription.his_lang.update({
    'fr_CH': {
        'M': [['son'] * 3, ['ses'] * 3],
        'F': [['sa'] * 3, ['ses'] * 3],
    },
    'de_DE': {
        'M': [['sein', 'seinen', 'seinem'], ['seine', 'seinen',
                                             'seinen']],
        'F': [['seine', 'seine', 'seiner'], ['seine', 'seinen',
                                             'seinen']],
    },
    'it_IT': {
        'M': [['suo'] * 3, ['i suoi'] * 3],
        'F': [['sua'] * 3, ['i suoi'] * 3],
    },
})


ChildDescription.he_lang.update({
    'fr_CH': {'M': [['il'] * 3, ['ils'] * 3],
              'F': [['elle'] * 3, ['elles'] * 3]},
    'de_DE': {'M': [['er'] * 3, ['sie'] * 3],
              'F': [['sie'] * 3, ['sie'] * 3]},
    'it_IT': {'M': [[''] * 3, [''] * 3],
              'F': [[''] * 3, [''] * 3]},
})


ChildDescription.home_based_lang.update({
    'fr_CH': {
        'M': u'{preferred_name} suit le programme à la maison pour '
             u'enfants en bas-âge.',
        'F': u'{preferred_name} suit le programme à la maison pour '
             u'enfants en bas-âge.',
    },
    'de_DE': {
        'M': u'{preferred_name} wird zu Hause im Programm für kleine '
             u'Kinder begleitet.',
        'F': u'{preferred_name} wird zu Hause im Programm für kleine '
             u'Kinder begleitet.',
    },
    'it_IT': {
        'M': u'{preferred_name} segue il programma a casa per i '
             u'bambini piccoli.',
        'F': u'{preferred_name} segue il programma a casa per i '
             u'bambini piccoli.',
    },
})


ChildDescription.school_yes_lang.update({
    'fr_CH': {
        'M': u"{preferred_name} va {level}.",
        'F': u"{preferred_name} va {level}.",
    },
    'de_DE': {
        'M': u'{preferred_name} geht {level}.',
        'F': u'{preferred_name} geht {level}.',
    },
    'it_IT': {
        'M': u'{preferred_name} frequenta {level}.',
        'F': u'{preferred_name} frequenta {level}.',
    },
})


ChildDescription.school_no_lang.update({
    'fr_CH': {
        'M': u"{preferred_name} ne va pas à l'école.",
        'F': u"{preferred_name} ne va pas à l'école.",
    },
    'de_DE': {
        'M': u'{preferred_name} geht nicht zur Schule.',
        'F': u'{preferred_name} geht nicht zur Schule.',
    },
    'it_IT': {
        'M': u'{preferred_name} non frequenta la scuola.',
        'F': u'{preferred_name} non frequenta la scuola.',
    },
})


ChildDescription.duties_intro_lang.update({
    'fr_CH': {
        'M': u"À la maison, il participe aux tâches suivantes :",
        'F': u"À la maison, elle participe aux tâches suivantes :",
    },
    'de_DE': {
        'M': u'Er hilft zu Hause:',
        'F': u'Sie hilft zu Hause:',
    },
    'it_IT': {
        'M': u'A casa aiuta nei seguenti compiti:',
        'F': u'A casa aiuta nei seguenti compiti:',
    },
})


ChildDescription.church_intro_lang.update({
    'fr_CH': {
        'M': u"À l'église, il participe aux activités suivantes :",
        'F': u"À l'église, elle participe aux activités suivantes :",
    },
    'de_DE': {
        'M': u'In der Kirche macht er mit bei:',
        'F': u'In der Kirche macht sie mit bei:',
    },
    'it_IT': {
        'M': u'In chiesa partecipa alle seguenti attività:',
        'F': u'In chiesa partecipa alle seguenti attività:',
    },
})


ChildDescription.hobbies_intro_lang.update({
    'fr_CH': {
        'M': u"Ses activités favorites sont :",
        'F': u"Ses activités favorites sont :",
    },
    'de_DE': {
        'M': u'Er mag gern:',
        'F': u'Sie mag gern:',
    },
    'it_IT': {
        'M': u'A {preferred_name} piace:',
        'F': u'A {preferred_name} piace:',
    },
})


ChildDescription.handicap_intro_lang.update({
    'fr_CH': {
        'M': u"{preferred_name} souffre de :",
        'F': u"{preferred_name} souffre de :",
    },
    'de_DE': {
        'M': u'{preferred_name} leidet unter:',
        'F': u'{preferred_name} leidet unter:',
    },
    'it_IT': {
        'M': u'{preferred_name} soffre di:',
        'F': u'{preferred_name} soffre di:',
    },
})


class ChildDescriptionCH(models.TransientModel):
    _inherit = 'compassion.child.description'

    @api.model
    def _supported_languages(self):
        """
        Inherit to add more languages to have translations of
        descriptions.
        {lang: description_field}
        """
        return {
            'en_US': 'desc_en',
            'de_DE': 'desc_de',
            'fr_CH': 'desc_fr',
            'it_IT': 'desc_it',
        }

    def his(self, gender, number=SINGULAR, tense=NOMINATIVE):
        result = super(ChildDescriptionCH, self).his(gender, number, tense)
        if self.env.lang == 'de_DE':
            # In german, "sein" becomes "ihr"
            result = self.child_id.get(result)
        return result
