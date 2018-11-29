# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models


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
            if registration.event_id.event_type_id == self.env.ref(
                    'website_event_compassion.event_type_group_visit'):
                registration.confirm_registration()
                # Mark down payment task as done
                task = self.env.ref(
                    'website_event_compassion.task_down_payment')
                transaction.registration_id.completed_task_ids += task
