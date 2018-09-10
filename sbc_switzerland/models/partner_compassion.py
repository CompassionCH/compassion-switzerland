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
            if not tc.selectOne("SELECT id FROM user WHERE number = %s",
                                translator.ref):
                translator.with_context(force_create=True).write(
                    {'ref': translator.ref})
                missing.append(translator.ref)
        return ','.join(missing)
