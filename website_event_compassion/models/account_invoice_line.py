##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, api, fields


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    registration_id = fields.Many2one(
        'event.registration', compute='_compute_registration',
        store=True
    )

    @api.multi
    @api.depends('user_id.registration_ids', 'event_id')
    def _compute_registration(self):
        for line in self:
            line.registration_id =\
                line.user_id.registration_ids.filtered(
                    lambda r: r.event_id == line.event_id
                )
