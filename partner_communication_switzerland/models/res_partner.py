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

from odoo import api, models, fields, _


class ResPartner(models.Model):
    """
    Add method to send all planned communication of sponsorships.
    """
    _name = 'res.partner'
    _inherit = ['res.partner', 'translatable.model']

    letter_delivery_preference = fields.Selection(
        selection='_get_delivery_preference',
        default='auto_digital',
        required=True,
        help='Delivery preference for Child Letters',
    )
    thankyou_preference = fields.Selection(
        compute='_compute_thankyou_preference', store=True
    )
    is_new_donor = fields.Boolean(compute='_compute_new_donor')
    ambassador_quote = fields.Html(
        help='Used in thank you letters for donations linked to an event '
             'and to this partner.',
    )

    @api.multi
    def _get_salutation(self):
        company = self.filtered(
            lambda p: not (p.title and p.firstname and not p.is_company))
        for p in company:
            p.salutation = _("Dear friends of compassion")
            p.short_salutation = p.salutation
        super(ResPartner, self - company)._get_salutation()

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
    def _compute_new_donor(self):
        invl_obj = self.env['account.invoice.line'].with_context(lang='en_US')
        donor = self.env.ref('partner_compassion.res_partner_category_donor')
        for partner in self:
            if donor in partner.category_id:
                partner.is_new_donor = False
                continue
            donation_invl = invl_obj.search([
                ('partner_id', '=', partner.id),
                ('state', '=', 'paid'),
                ('product_id.categ_name', '!=', "Sponsorship")
            ])
            payments = donation_invl.mapped('last_payment')
            new_donor = len(payments) < 2 and not partner.has_sponsorships
            partner.is_new_donor = new_donor
