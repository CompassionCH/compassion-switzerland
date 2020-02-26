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
from odoo import api, fields
from . import translate_connector
from odoo.addons.base_geoengine import geo_model


_logger = logging.getLogger(__name__)


class AdvocateDetails(geo_model.GeoModel):
    _inherit = 'advocate.details'

    translator_since = fields.Datetime()
    translated_letter_ids = fields.One2many(
        'correspondence', related='partner_id.translated_letter_ids')
    nb_translated_letters = fields.Integer(
        compute='_compute_nb_translated_letters', store=True)

    @api.multi
    @api.depends('partner_id.translated_letter_ids')
    def _compute_nb_translated_letters(self):
        for advocate in self:
            advocate.nb_translated_letters = len(
                advocate.translated_letter_ids)

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        translation = self.env.ref('partner_compassion.engagement_translation')
        advocate = super().create(vals)
        if translation in advocate.engagement_ids:
            advocate._insert_new_translator()
        return advocate

    @api.multi
    def write(self, vals):
        translation = self.env.ref('partner_compassion.engagement_translation')
        goodbye_config = self.env.ref('sbc_switzerland.translator_goodbye')
        for advocate in self:
            was_translator = translation in advocate.engagement_ids
            super(AdvocateDetails, advocate).write(vals)
            is_translator = translation in advocate.engagement_ids
            if not was_translator and is_translator:
                advocate._insert_new_translator()

            if was_translator and not is_translator:
                tc = translate_connector.TranslateConnect()
                _logger.info(
                    "translator tag removed, we delete any user in "
                    "translation platform with that ref as number")
                try:
                    tc.remove_user(advocate.partner_id)
                except Exception:
                    _logger.warning("Couldn't remove user: ", exc_info=True)
                    tc.disable_user(advocate.partner_id)
                finally:
                    self.env['partner.communication.job'].create({
                        'config_id': goodbye_config.id,
                        'partner_id': advocate.partner_id.id,
                        'object_ids': advocate.partner_id.id,
                    })
        return True

    def set_inactive(self):
        # Inactivate translator from platform
        translation = self.env.ref('partner_compassion.engagement_translation')
        if translation in self.engagement_ids and not self.env.context.get(
                'skip_translation_platform_update'):
            tc = translate_connector.TranslateConnect()
            goodbye_config = self.env.ref('sbc_switzerland.translator_goodbye')
            _logger.info(
                "translator put inactive, we inactivate in "
                "translation platform.")
            try:
                tc.disable_user(self.partner_id)
            except Exception:
                _logger.error("couldn't disable translator", exc_info=True)
            finally:
                self.env['partner.communication.job'].create({
                    'config_id': goodbye_config.id,
                    'partner_id': self.partner_id.id,
                    'object_ids': self.partner_id.id,
                })
        return super().set_inactive()

    def set_active(self):
        translation = self.env.ref('partner_compassion.engagement_translation')
        if translation in self.engagement_ids and not self.env.context.get(
                'skip_translation_platform_update'):
            tc = translate_connector.TranslateConnect()
            _logger.info("translator activated, put it again "
                         "in translation platform")
            tc.upsert_user(self.partner_id, create=False)
        return super().set_active()

    def unlink(self):
        # Remove from translation platform
        translation = self.env.ref('partner_compassion.engagement_translation')
        tc = translate_connector.TranslateConnect()
        goodbye_config = self.env.ref('sbc_switzerland.translator_goodbye')
        _logger.info(
            "translator deleted, we delete any user in "
            "translation platform with that ref as number")
        for advocate in self:
            if translation in advocate.engagement_ids and not \
                    self.env.context.get('skip_translation_platform_update'):
                try:
                    tc.remove_user(advocate.partner_id)
                except Exception:
                    _logger.warning("Couldn't remove user: ", exc_info=True)
                    tc.disable_user(advocate.partner_id)
                finally:
                    self.env['partner.communication.job'].create({
                        'config_id': goodbye_config.id,
                        'partner_id': advocate.partner_id.id,
                        'object_ids': advocate.partner_id.id,
                    })
        return super().unlink()

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def translated_letters(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Letters',
            'res_model': 'correspondence',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'context': self.with_context(
                group_by=False,
                search_default_translator_id=self.partner_id.id
            ).env.context,
        }

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _insert_new_translator(self):
        tc = translate_connector.TranslateConnect()
        _logger.info("Insert translator on platform.")
        try:
            tc.upsert_user(self.partner_id, create=True)
        except:
            _logger.warning("Couldn't upsert user: ", exc_info=True)
            tc.upsert_user(self.partner_id, create=False)

        # The translation platform sends an activation email to all the users
        # that match every one of the following conditions:
        #   - alertTranslator = 1
        #   - code is NULL
        #   - password is NULL
        #   - last_login is NULL

        if not self.partner_id.has_agreed_child_protection_charter:
            tc.disable_user(self.partner_id)

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
        self.translator_since = fields.Datetime.now()

    ##########################################################################
    #                              ACTION RULES                              #
    ##########################################################################
    @api.multi
    def send_welcome_translator(self):
        communication_config = self.env.ref(
            'sbc_switzerland.new_translator_welcome')
        for advocate in self:
            self.env['partner.communication.job'].create({
                'config_id': communication_config.id,
                'partner_id': advocate.partner_id.id,
                'object_ids': advocate.partner_id.id,
            })
