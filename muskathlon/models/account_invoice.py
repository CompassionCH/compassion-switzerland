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


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _after_transaction_invoice_paid(self, transaction):
        """
        Confirm registration when it's paid.
        :param transaction: payment.transaction record
        :return: None
        """
        super(AccountInvoice, self)._after_transaction_invoice_paid(
            transaction)
        registration = transaction.registration_id
        if registration:
            if registration.event_id.event_type_id == \
                    self.env.ref('muskathlon.event_type_muskathlon'):
                registration.confirm_registration()
                # Check all tasks already done
                tasks = self.env.ref('muskathlon.task_down_payment')
                partner = registration.partner_id
                advocate = partner.advocate_details_id
                if partner.user_ids.state == 'active':
                    tasks += self.env.ref('muskathlon.task_activate_account')
                if registration.passport_number and \
                        registration.emergency_name:
                    tasks += self.env.ref('muskathlon.task_passport')
                if advocate.picture_large:
                    tasks += self.env.ref('muskathlon.task_picture')
                registration.completed_task_ids += tasks


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    sent_to_4m = fields.Date('Sent to 4M', copy=False)
    price_cents = fields.Float(compute='_compute_amount_cents')

    @api.multi
    def _compute_amount_cents(self):
        for line in self:
            line.price_cents = line.price_subtotal*100
