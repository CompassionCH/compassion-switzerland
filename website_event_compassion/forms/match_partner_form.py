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

    class EventPartnerMatchform(models.AbstractModel):

        _name = 'cms.form.event.match.partner'
        _inherit = 'cms.form.match.partner'

        def _get_partner_vals(self, values, extra_values):
            keys = super(EventPartnerMatchform, self)._get_partner_vals(
                values, extra_values
            )
            keys.update({'state': 'pending'})
            return keys
