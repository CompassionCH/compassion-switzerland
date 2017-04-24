# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import logging

from openerp import http, fields
from openerp.tools import mod10r
from openerp.http import request


_logger = logging.getLogger(__name__)


OK_RESULTS = {
    'en_US': 'We successfully received your authorization. The amount will '
             'be withdrawn from your account in the next 3 days.',
    'fr_CH': 'Nous avons bien reçu votre autorisation de débit. Le montant '
             'sera prélevé de votre compte dans les  3 prochains jours.',
    'de_DE': 'Sie haben uns Ihre Genehmigung erfolgreich übermittelt. Der '
             'Betrag wird in den nächsten drei Tagen von Ihrem Konto '
             'abgebucht.',
    'it_IT': 'Abbiamo ricevuto la vostra autorizzazione. La somma sarà '
             'prelevata dal vostro conto nei prossimi 3 giorni.'
}

FAIL_RESULTS = {
    'en_US': "We couldn't verify your information. Only one debit can be "
             "sent per day. If you have trouble sending your gift, please "
             "contact the office.",
    'fr_CH': "Nous n'avons pas pu vérifier vos informations. Nous "
             "n'autorisons qu'une seule demande par jour. Si vous avez des "
             "difficultés à envoyer votre don, veuillez nous contacter.",
    'de_DE': 'Wir konnten Ihre Informationen nicht verifizieren. Wir '
             'erlauben nur eine einzige Belastungsanfrage pro Tag. Falls Sie '
             'Schwierigkeiten mit dem Senden Ihres Geschenks haben, '
             'kontaktieren Sie uns bitte.',
    'it_IT': 'Non siamo riusciti a verificare i vostri dati. Puó essere '
             'inviato al giorno solo un addebito. In caso di problemi di '
             'invio del dono, vi preghiamo di contattarci.'
}


class GenerateChristmasInvoice(http.Controller):
    """ Add URL Handler for Creating Christmas Invoices.
    """
    @http.route('/christmas/invoice', type='http', auth='public', methods=[
        'POST'])
    def handler_christmas(self, uuid, amount, **kwargs):
        _logger.info("Christmas Gift received: %s" % uuid + ' ' + amount)
        partner = request.env['res.partner'].sudo().search([
            ('uuid', '=', uuid)
        ])
        if len(partner) == 1:
            mandate = request.env['account.banking.mandate'].sudo().search([
                ('partner_bank_id.partner_id', '=', partner.id),
                ('state', '=', 'valid')
            ], limit=1)
            product = request.env['product.product'].sudo().with_context(
                lang='en_US').search([
                    ('name', '=', 'Christmas Gift Fund')])
            # Verify an invoice line is not already open on the same day
            invl = request.env['account.invoice.line'].sudo().search([
                ('product_id', '=', product.id),
                ('partner_id', '=', partner.id),
                ('state', '=', 'open'),
                ('due_date', '=', fields.Date.today())
            ])
            if mandate and not invl:
                journal = request.env['account.journal'].sudo().search([
                    ('type', '=', 'sale'),
                    ('company_id', '=', 1)
                ], limit=1)
                payment_term = False
                if mandate.partner_bank_id.state == 'bv':
                    payment_term = request.env.ref(
                        'contract_compassion.payment_term_postfinance_dd')
                elif mandate.partner_bank_id.state == 'iban':
                    payment_term = request.env.ref(
                        'contract_compassion.payment_term_lsv')
                analytic_account = request.env[
                    'account.analytic.account'].sudo().search([
                        ('name', '=', 'Christmas Campaign')
                    ])

                invoice = request.env['account.invoice'].sudo().create({
                    'account_id': partner.property_account_receivable.id,
                    'type': 'out_invoice',
                    'partner_id': partner.id,
                    'journal_id': journal.id,
                    'currency_id':
                        partner.property_product_pricelist.currency_id.id,
                    'date_invoice': fields.Date.today(),
                    'payment_term': payment_term.id,
                    'bvr_reference': self._generate_bvr_reference(
                        partner, payment_term),
                    'origin': 'Christmas Web Payment',
                    'invoice_line': [(0, 0, {
                        'name': product.name,
                        'price_unit': amount,
                        'quantity': 1,
                        'uos_id': False,
                        'product_id': product.id,
                        'account_id': product.property_account_income.id,
                        'account_analytic_id': analytic_account.id,
                    })]
                })
                if invoice:
                    invoice.signal_workflow('invoice_open')
                    OK_RESULTS['fr_FR'] = OK_RESULTS['fr_CH']
                    return OK_RESULTS.get(request.lang, OK_RESULTS['en_US'])

        FAIL_RESULTS['fr_FR'] = FAIL_RESULTS['fr_CH']
        return FAIL_RESULTS.get(request.lang, FAIL_RESULTS['en_US'])

    def _generate_bvr_reference(self, partner, payment_term):
        ref = partner.ref
        bvr_reference = '0' * (9 + (7 - len(ref))) + ref
        # Not related to a sponsorship -> NumPole is 0
        bvr_reference += '0' * 5
        # Type for campaign
        bvr_reference += '7'
        # Christmas fund id
        bvr_reference += '0' * 2
        bvr_reference += '23'

        if 'LSV' in payment_term.sudo().name:
            # Get company BVR adherent number
            company = request.env['res.company'].sudo().browse(1)
            bank_obj = request.env['res.partner.bank'].sudo()
            company_bank = bank_obj.search([
                ('partner_id', '=', company.partner_id.id),
                ('bvr_adherent_num', '!=', False)])
            if company_bank:
                bvr_reference = company_bank.bvr_adherent_num + \
                    bvr_reference[9:]
        if len(bvr_reference) == 26:
            return mod10r(bvr_reference)
