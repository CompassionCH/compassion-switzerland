# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015-2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, api, _

from odoo.addons.report_compassion.models.contract_group import setlocale

from odoo.exceptions import UserError


class PaymentOrder(models.Model):
    _inherit = "account.payment.order"

    @api.multi
    def draft2open(self):
        """
        Check the partner bank
        Logs a note in invoices when imported in payment order
        """
        for order in self:
            for line in order.payment_line_ids:
                if line.partner_bank_id not in line.partner_id.bank_ids:
                    raise UserError(
                        _("The bank account %s is not related to %s.")
                        % (line.partner_bank_id.acc_number,
                           line.partner_id.name)
                    )
            mode = order.payment_mode_id.name
            for invoice in order.mapped(
                    'payment_line_ids.move_line_id.invoice_id'):

                url = '<a href="web#id={}&view_type=form&model=account.' \
                      'payment.order&action=1174">{}</a>'.\
                    format(order.id, order.name)

                invoice.message_post(
                    _((('The invoice has been imported in '
                        'a %s payment order : ') % mode) + url))

        return super(PaymentOrder, self).draft2open()

    @api.multi
    def action_cancel(self):
        """ Logs a note in invoices when order is cancelled. """
        for order in self:
            mode = order.payment_mode_id.name
            for invoice in order.mapped(
                    'payment_line_ids.move_line_id.invoice_id'):
                invoice.message_post(
                    _('The %s order has been cancelled.' % mode))

        return super(PaymentOrder, self).action_cancel()

    @api.model
    def _prepare_bank_payment_line(self, paylines):
        """
        Change communication of payment lines.
        :param paylines: account.payment.line recordset
        :return: dict for bank.payment.line creation
        """
        res = super(PaymentOrder, self)._prepare_bank_payment_line(paylines)
        partner = paylines.mapped('partner_id')

        return self.with_context(lang=partner.lang) \
            ._prepare_bank_payment_line_with_lang(paylines, partner, res)

    @api.model
    def _prepare_bank_payment_line_with_lang(self, paylines, partner, res):
        with setlocale(partner.lang):
            invoices = paylines.mapped('move_line_id.invoice_id').with_context(
                lang=partner.lang)
            products = invoices.mapped('invoice_line_ids.product_id')
            invoice_type = list(set(invoices.mapped('invoice_type')))
            invoice_type = invoice_type and invoice_type[0] or 'other'
            communication = False
            if invoice_type in ('sponsorship', 'gift'):
                children = invoices.mapped(
                    'invoice_line_ids.contract_id.child_id')
                if len(children) == 1:
                    if invoice_type == 'sponsorship':
                        communication = _('Sponsorship')
                    elif len(products) == 1:
                        communication = products.name + ' ' + _('for')
                    else:
                        communication = _('sponsorship gifts').title() + \
                            ' ' + _('for')
                    communication += ' ' + children.preferred_name
                else:
                    communication = str(len(children)) + ' '
                    if invoice_type == 'sponsorship':
                        communication += _('sponsorships')
                    else:
                        communication += _('sponsorship gifts')

                if invoice_type == 'sponsorship':
                    communication += ' ' + _('Period: ')
                    if len(invoices) < 4:
                        communication += invoices.get_date('date_invoice',
                                                           '%B')
                    else:
                        communication += str(len(invoices)) + ' ' + _('months')
            elif len(products) == 1:
                communication = products.name

            if communication:
                res['communication'] = communication

        return res
