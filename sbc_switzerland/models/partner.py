##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import functools
from odoo import api, models
from . import translate_connector


class ResPartner(models.Model):
    """
    This class augment the write method to update the translation platform. If
    the partner is also a translator.
    It also override the agree_to_child_protection_charter method to activate
    the associated translator advocate.
    """
    _inherit = 'res.partner'

    @api.multi
    def write(self, vals):
        res = super().write(vals)

        translation = self.env.ref('partner_compassion.engagement_translation')

        for partner in self:
            if translation in partner.engagement_ids:
                tc_values = ['lang', 'ref', 'email', 'firstname', 'lastname']
                tc_change = functools.reduce(
                    lambda x, y: x or y, [v in vals for v in tc_values])

                if tc_change:
                    tc = translate_connector.TranslateConnect()
                    # _logger.info("translator tag still present, we update "
                    #              "partner in translation platform")
                    tc.upsert_user(partner, create=False)

        return res

    @api.multi
    def agree_to_child_protection_charter(self):
        res = super().agree_to_child_protection_charter()
        translation = self.env.ref('partner_compassion.engagement_translation')
        for partner in self:
            advocate = partner.advocate_details_id
            if translation in advocate.engagement_ids:
                advocate.set_active()
        return res
