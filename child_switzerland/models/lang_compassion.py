# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp import api, models


class CompassionChild(models.Model):
    _inherit = 'res.lang.compassion'

    @api.model
    def lang_ch_install(self):
        langs = self.env['res.lang'].search([]).mapped('code')
        for lang in ['fr_CH', 'de_DE', 'it_IT']:
            if lang not in langs:
                self.env['base.language.install'].create({
                    'lang': lang
                }).lang_install()
        return True
