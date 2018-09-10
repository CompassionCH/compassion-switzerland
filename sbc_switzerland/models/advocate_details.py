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
from odoo import api, models
from . import translate_connector

_logger = logging.getLogger(__name__)


class AdvocateDetails(models.Model):
    _inherit = 'advocate.details'

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.multi
    def write(self, vals):
        translation_id = self.env.ref(
            'partner_compassion.engagement_translation').id
        for advocate in self:
            was_translator = translation_id in advocate.engagement_ids.ids
            if self._context.get('force_create'):
                was_translator = False
            super(AdvocateDetails, advocate).write(vals)
            is_translator = translation_id in advocate.engagement_ids.ids
            if not was_translator and is_translator:
                tc = translate_connector.TranslateConnect()
                _logger.info("translator tag added, we insert partner in "
                             "translation platform and prepare a welcome "
                             "communication")
                try:
                    tc.upsert_user(advocate.partner_id, create=True)
                except:
                    tc.upsert_user(advocate.partner_id, create=False)

                # prepare welcome communication
                config = self.env.ref(
                    'sbc_switzerland.new_translator_config')
                self.env['partner.communication.job'].create({
                    'config_id': config.id,
                    'partner_id': advocate.partner_id.id,
                    'object_ids': advocate.partner_id.id,
                    'user_id': config.user_id.id,
                    'show_signature': True,
                    'print_subject': True
                })

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
