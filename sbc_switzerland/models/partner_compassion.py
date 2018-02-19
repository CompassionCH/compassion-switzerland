# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Jonathan Kläy <jonathan@klay.swiss>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from odoo import api, models
from . import translate_connector

logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    """ This class upgrade the partners to match Compassion needs.
        It also synchronize all changes with the MySQL server of GP.
    """
    _inherit = 'res.partner'

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, values):
        partner = super(ResPartner, self.with_context(
            force_create=True)).create(values)
        return partner

    @api.multi
    def write(self, values):
        translator_id = self.env.ref(
            'partner_compassion.res_partner_category_translator').id
        for partner in self:
            was_translator = translator_id in partner.category_id.ids
            if self._context.get('force_create'):
                was_translator = False
            super(ResPartner, partner).write(values)
            is_translator = translator_id in partner.category_id.ids
            if not was_translator and is_translator:
                tc = translate_connector.TranslateConnect()
                logger.info("translator tag added, we insert partner in "
                            "translation platform")
                try:
                    tc.upsert_user(partner, create=True)
                except:
                    tc.upsert_user(partner, create=False)
            if was_translator and is_translator:
                tc_values = ['name', 'email', 'ref', 'lang', 'firstname',
                             'lastname']
                tc_change = reduce(
                    lambda x, y: x or y, [v in values for v in tc_values])
                if tc_change:
                    tc = translate_connector.TranslateConnect()
                    logger.info("translator tag still present, we update "
                                "partner in translation platform")
                    tc.upsert_user(partner, create=False)
            if was_translator and not is_translator:
                tc = translate_connector.TranslateConnect()
                logger.info("translator tag removed, we delete any user in "
                            "translation platform with that ref as number")
                try:
                    tc.remove_user(partner)
                except:
                    tc.disable_user(partner)
        return True
    
    @api.model
    def find_missing_translator(self):
        translator_id = self.env.ref(
            'partner_compassion.res_partner_category_translator').id
        translators = self.search([
            ('category_id', '=', translator_id)
        ])
        tc = translate_connector.TranslateConnect()
        missing = list()
        for translator in translators:
            if not tc.selectOne("SELECT id FROM user WHERE number = %s", translator.ref):
                translator.with_context(force_create=True).write({'ref': translator.ref})
                missing.append(translator.ref)
        return ','.join(missing)
