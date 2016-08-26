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
        self.pays_christmas_fund = False
        for contract_line in \
                self.other_contract_ids.contract_line_ids.with_context(
                    lang='en_US'):
            if contract_line.product_id.\
                    name_template == 'Christmas Gift Fund':
                self.pays_christmas_fund = True
                break
