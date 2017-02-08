# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import api, models, fields, _


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    thankyou_preference = fields.Selection(
        selection='_get_delivery_preference', compute='_get_preference',
        store=True
    )

    @api.multi
    @api.depends('thankyou_letter')
    def _get_preference(self):
        """
        Converts old preference into communication preference.
        """
        thankyou_mapping = {
            'no': 'none',
            'default': 'auto_digital',
            'paper': 'physical'
        }
        for partner in self:
            partner.thankyou_preference = thankyou_mapping[
                partner.thankyou_letter]
