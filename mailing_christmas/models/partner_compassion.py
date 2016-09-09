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
from openerp import api, fields, models


class ResPartner(models.Model):
    """ Add Partner UUID
    """

    _inherit = 'res.partner'

    uuid = fields.Char(compute='compute_uuid', store=True)
    pays_christmas_fund = fields.Boolean(
        compute='compute_pays_christmas_fund')

    _sql_constraints = [
        ('unique_uuid', 'unique(uuid)', 'Partner UUID must be unique!')
    ]

    @api.depends('ref')
    @api.multi
    def compute_uuid(self):
        for partner in self:
            partner.uuid = uuid.uuid4()

    @api.multi
    def compute_pays_christmas_fund(self):
        for partner in self:
            lines = partner.other_contract_ids.with_context(
                lang='en_US').mapped(
                'contract_line_ids.product_id.name_template')
            partner.pays_christmas_fund = 'Christmas Gift Fund' in lines

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
