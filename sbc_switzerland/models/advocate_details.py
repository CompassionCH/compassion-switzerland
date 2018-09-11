# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Maxime Beck <mbcompte@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from odoo import api
from odoo.addons.base_geoengine import geo_model
from . import translate_connector

_logger = logging.getLogger(__name__)


class AdvocateDetails(geo_model.GeoModel):
    _inherit = 'advocate.details'

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        translation = self.env.ref('partner_compassion.engagement_translation')
        advocate = super(AdvocateDetails, self).create(vals)
        if translation in advocate.engagement_ids:
            advocate._insert_translator()
        return advocate

    @api.multi
    def write(self, vals):
        translation = self.env.ref('partner_compassion.engagement_translation')
        for advocate in self:
            was_translator = translation in advocate.engagement_ids
            super(AdvocateDetails, advocate).write(vals)
            is_translator = translation in advocate.engagement_ids
            if not was_translator and is_translator:
                advocate._insert_translator()

            if was_translator and is_translator:
                tc_values = ['name', 'email', 'ref', 'lang', 'firstname',
                             'lastname']
                tc_change = reduce(
                    lambda x, y: x or y, [v in vals for v in tc_values])
                if tc_change:
                    tc = translate_connector.TranslateConnect()
                    _logger.info("translator tag still present, we update "
                                 "partner in translation platform")
                    tc.upsert_user(advocate.partner_id, create=False)
            if was_translator and not is_translator:
                tc = translate_connector.TranslateConnect()
                _logger.info(
                    "translator tag removed, we delete any user in "
                    "translation platform with that ref as number")
                try:
                    tc.remove_user(advocate.partner_id)
                except:
                    tc.disable_user(advocate.partner_id)
        return True

    def _insert_translator(self):
        tc = translate_connector.TranslateConnect()
        _logger.info("Insert translator on platform.")
        try:
            tc.upsert_user(self.partner_id, create=True)
        except:
            tc.upsert_user(self.partner_id, create=False)
        # prepare welcome communication
        config = self.env.ref('sbc_switzerland.new_translator_config')
        self.env['partner.communication.job'].create({
            'config_id': config.id,
            'partner_id': self.partner_id.id,
            'object_ids': self.partner_id.id,
            'user_id': config.user_id.id,
            'show_signature': True,
            'print_subject': True
        })
