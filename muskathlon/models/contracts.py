##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#    @author: Sebastien Toth <popod@me.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields, api


class RecurringContract(models.Model):
    _inherit = "recurring.contract"

    sent_to_4m = fields.Date('Sent to 4M', copy=False)

    registration_id = fields.Many2one(
        'event.registration', compute='_compute_muskathlon_registration',
        store=True
    )

    @api.multi
    @api.depends('user_id.registration_ids', 'origin_id.event_id')
    def _compute_muskathlon_registration(self):
        for contract in self:
            contract.registration_id = \
                contract.user_id.registration_ids.filtered(
                    lambda r: r.event_id == contract.origin_id.event_id
                )
