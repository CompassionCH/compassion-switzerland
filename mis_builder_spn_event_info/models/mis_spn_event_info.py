# Copyright 2018-2020 Compassion Suisse
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
from os.path import join as opj

from odoo import api, fields, models, tools


class MisSpnEventInfo(models.Model):

    _name = 'mis.spn_event.info'
    _description = 'MIS Sponsorship and Events info'
    _auto = False

    line_type = fields.Char()
    name = fields.Char()
    account_id = fields.Many2one(
        comodel_name='account.account',
        string='Account',
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
    )
    invoice_id = fields.Many2one(
        'account.invoice',
        string='Invoice',
    )
    event_id = fields.Many2one(
        'crm.event.compassion',
        string='Event',
    )
    event_type_id = fields.Many2one(
        'event.type',
        string='Event type',
    )
    user_id = fields.Many2one(
        'res.partner',
        string='Ambassador',
    )
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic account',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
    )
    credit = fields.Float()
    debit = fields.Float()
    date = fields.Date()

    @api.model_cr
    def init(self):
        script = opj(os.path.dirname(__file__), 'mis_spn_event_info.sql')
        with open(script) as f:
            tools.drop_view_if_exists(self.env.cr, 'mis_spn_event_info')
            self.env.cr.execute(f.read())
