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
import uuid
from openerp import api, fields, models, _

M_PREFIX = {
    'fr_CH': u'Cher',
    'de_DE': u'Sehr geehrter',
    'it_IT': u'Caro',
    'en_US': u'Dear',
}

F_PREFIX = {
    'fr_CH': u'Chère',
    'de_DE': u'Sehr geehrte',
    'it_IT': u'Cara',
    'en_US': u'Dear',
}

P_PREFIX = {
    'fr_CH': u'Chers',
    'de_DE': u'Sehr geehrte',
    'it_IT': u'Cari',
    'en_US': u'Dear',
}

FP_PREFIX = {
    'fr_CH': u'Chères',
    'de_DE': u'Sehr geehrte',
    'it_IT': u'Cari',
    'en_US': u'Dear',
}


class ResPartner(models.Model):
    """ Add Partner UUID
    """

    _inherit = 'res.partner'

    uuid = fields.Char(compute='compute_uuid', store=True)
    pays_christmas_fund = fields.Boolean(
        compute='_compute_christmas_fund')
    christmas_amount = fields.Float(
        compute='_compute_christmas_fund')
    salutation = fields.Char(
        compute='_compute_salutation'
    )
    active_sponsorships = fields.One2many(
        'recurring.contract', compute='_compute_active_sponsorships'
    )
    child_name = fields.Char(compute='_compute_active_sponsorships')

    _sql_constraints = [
        ('unique_uuid', 'unique(uuid)', 'Partner UUID must be unique!')
    ]

    @api.depends('ref')
    @api.multi
    def compute_uuid(self):
        for partner in self:
            partner.uuid = uuid.uuid4()

    @api.multi
    def _compute_christmas_fund(self):
        for partner in self:
            lines = partner.other_contract_ids.filtered(
                lambda c: c.state not in ('terminated',
                                          'cancelled')).with_context(
                lang='en_US').mapped('contract_line_ids').filtered(
                lambda l: l.product_id.name_template == 'Christmas Gift Fund')
            partner.pays_christmas_fund = bool(lines)
            partner.christmas_amount = sum(lines.mapped('subtotal'))

    @api.multi
    def _compute_salutation(self):
        lang = self.env.lang or 'en_US'
        for partner in self:
            if partner.title.id in [5, 6, 7, 30]:
                prefix = M_PREFIX[lang]
            elif partner.title.id in [3, 29]:
                prefix = F_PREFIX[lang]
            elif partner.title.id == 25:
                prefix = FP_PREFIX[lang]
            else:
                prefix = P_PREFIX[lang]
            if partner.title.name:
                title = partner.title.name.lower() + u' ' if lang != 'de_DE' \
                    else partner.title.name + u' '
            else:
                title = u''
            partner.salutation = prefix + u' ' + title + partner.lastname

    @api.multi
    def _compute_active_sponsorships(self):
        for partner in self:
            active_sponsorships = self.env['recurring.contract'].search([
                '|', ('correspondant_id', '=', partner.id),
                ('partner_id', '=', partner.id),
                ('type', 'in', ['S', 'SC']),
                ('state', 'not in', ['terminated', 'cancelled']),
            ])
            if len(active_sponsorships) == 1:
                name = active_sponsorships.child_id.firstname
                if self.env.lang == 'it_IT':
                    name = 'di ' + name
                partner.child_name = name
            elif active_sponsorships:
                partner.child_name = _("your sponsored children")
            partner.active_sponsorships = active_sponsorships

    @api.model
    def update_partner_payment_terms(self):
        """ Function to call with ERPPEEK to update all partner payment
            terms based on their sponsorship payment preferences.
        """
        partners = self.search([('customer', '=', True)])
        for partner in partners:
            contract = self.env['recurring.contract'].search([
                ('partner_id', '=', partner.id),
                ('state', '=', 'active')
            ], limit=1)
            if contract:
                partner.property_payment_term = contract.payment_term_id
        return True
