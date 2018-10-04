# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#    @author: Sebastien Toth <popod@me.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, api, fields


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    sent_to_4m = fields.Date('Sent to 4M')
    price_cents = fields.Float(compute='_compute_amount_cents')
    registration_id = fields.Many2one(
        'event.registration', compute='_compute_muskathlon_registration',
        store=True
    )

    @api.multi
    @api.depends('user_id.registration_ids', 'event_id')
    def _compute_muskathlon_registration(self):
        for line in self:
            line.registration_id =\
                line.user_id.registration_ids.filtered(
                    lambda r: r.event_id == line.event_id
                )

    @api.multi
    def _compute_amount_cents(self):
        for line in self:
            line.price_cents = line.price_subtotal*100
