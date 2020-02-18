##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields


class ResPartnerCategory(models.Model):
    """
    Warn user when making a sponsorship for sponsor that has a category.
    """
    _inherit = 'res.partner.category'

    warn_sponsorship = fields.Boolean()


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_restricted = fields.Boolean(compute='_compute_is_restricted')

    def _compute_is_restricted(self):
        restricted_category = self.env.ref(
            'sponsorship_switzerland.res_partner_restricted')
        for partner in self:
            partner.is_restricted = restricted_category in partner.category_id
