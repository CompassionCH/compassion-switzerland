# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Maxime Beck
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models


class MuskathlonPartnerMatchform(models.AbstractModel):

    _name = 'cms.form.muskathlon.match.partner'
    _inherit = 'cms.form.match.partner'

    def _get_partner_vals(self, values, extra_values):
        keys = super(MuskathlonPartnerMatchform, self)._get_partner_vals(
            values, extra_values
        )
        keys.update({'state': 'pending'})
        return keys
