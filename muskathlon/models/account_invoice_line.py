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

    sent_to_4m = fields.Date("Sent to 4M", copy=False)
    price_cents = fields.Float(compute="_compute_amount_cents")

    @api.multi
    def _compute_amount_cents(self):
        for line in self:
            line.price_cents = line.price_subtotal * 100

    @api.multi
    def _get_ambassador_receipt_config(self):
        """
        Check if donation is linked to a Muskathlon event.
        :return: partner.communication.config record
        """
        ambassador = self.mapped("user_id")
        muskathlon_event = self.mapped("event_id").filtered("website_muskathlon")
        if muskathlon_event and ambassador.advocate_details_id.mail_copy_when_donation:
            return self.env.ref(
                "muskathlon.ambassador_donation_confirmation_config"
            )
        return super()._get_ambassador_receipt_config()
