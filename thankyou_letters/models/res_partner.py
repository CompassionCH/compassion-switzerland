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

from openerp import api, models, fields


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    thankyou_preference = fields.Selection(
        selection='_get_delivery_preference',
        compute='_compute_thankyou_preference',
        store=True
    )
    is_new_donator = fields.Boolean(compute='_compute_new_donator')
    ambassador_quote = fields.Html(
        help='Used in thank you letters for donations linked to an event '
             'and to this partner.',
        translate=True
    )

    @api.multi
    @api.depends('thankyou_letter')
    def _compute_thankyou_preference(self):
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

    @api.multi
    def _compute_new_donator(self):
        invl_obj = self.env['account.invoice.line'].with_context(lang='en_US')
        donator = self.env.ref('partner_compassion.res_partner_category_donor')
        for partner in self:
            if donator in partner.category_id:
                partner.is_new_donator = False
                continue
            donation_invl = invl_obj.search([
                ('partner_id', '=', partner.id),
                ('state', '=', 'paid'),
                ('product_id.categ_name', '!=', "Sponsorship")
            ])
            payments = donation_invl.mapped('last_payment')
            partner.is_new_donator = payments and len(payments) < 2 and not \
                partner.has_sponsorships
