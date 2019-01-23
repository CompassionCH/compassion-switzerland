# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models
from odoo.addons.queue_job.job import job


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    @job
    def modify_open_invoice(self, vals):
        """
        Job for changing an open invoice with new values. It will put it back
        in draft, modifiy the invoice, and validate again the invoice.
        :param vals: dictionary with values to write
        :return: True
        """
        self.action_invoice_cancel()
        self.action_invoice_draft()
        self.write(vals)
        self.action_invoice_open()
        return True

    def action_invoice_paid(self):
        """
        Mark payment done if invoice is related to event registration
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
        # Mark group visit trip payment done
        registrations = self.env['event.registration'].sudo().search([
            ('group_visit_invoice_id', 'in', self.ids)
        ])
        task = self.env.ref(
            'website_event_compassion.task_full_payment')
        registrations.write({
            'completed_task_ids': [(4, task.id)]
        })
        return res
