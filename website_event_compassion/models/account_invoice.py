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

    def action_invoice_paid(self):
        """
        Mark down payment done if invoice is related to event registration
        """
        res = super(AccountInvoice, self).action_invoice_paid()
        registrations = self.env['event.registration'].sudo().search([
            ('down_payment_id', 'in', self.ids)
        ])
        registrations.confirm_registration()
        # Mark down payment task as done
        task = self.env.ref(
            'website_event_compassion.task_down_payment')
        registrations.write({
            'completed_task_ids': [(4, task.id)]
        })
        return res
