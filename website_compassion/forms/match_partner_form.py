# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Maxime Beck
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, tools

testing = tools.config.get('test_enable')

if not testing:
    # prevent these forms to be registered when running tests

    class PartnerMatchform(models.AbstractModel):

        _inherit = 'cms.form.match.partner'

        def form_before_create_or_update(self, values, extra_values):
            """
            Avoid updating partner at GMC, use context to prevent this.
            """
            super(
                PartnerMatchform,
                self.with_context(no_upsert=True)
            ).form_before_create_or_update(values, extra_values)
