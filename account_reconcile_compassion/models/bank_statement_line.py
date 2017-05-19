# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import api, models, exceptions, _
from openerp.tools import mod10r, DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.addons.sponsorship_compassion.models.product import \
    GIFT_CATEGORY, GIFT_NAMES, SPONSORSHIP_CATEGORY

from datetime import datetime

from openerp.addons.connector.queue.job import job, related_action
# from openerp.addons.connector.session import ConnectorSession


class BankStatement(models.Model):
    _inherit = 'account.bank.statement'

    @api.multi
    def button_confirm_bank(self):
        return super(BankStatement, self.with_context(
            async_mode=False)).button_confirm_bank()


class BankStatementLine(models.Model):

    _inherit = 'account.bank.statement.line'

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def get_reconciliation_proposition(self, excluded_ids=None):
        """ Never propose reconciliation when move_lines have not
            the same reference.
        """
        res = super(BankStatementLine, self).get_reconciliation_proposition(
            excluded_ids)
        return res.filtered(
            lambda mvl: mvl.ref == self.ref or
            mvl.user_type_id.type == 'payable'
        )

    @api.multi
    def get_move_lines_for_reconciliation(
            self, excluded_ids=None, str=False, offset=0, limit=None,
            additional_domain=None, overlook_partner=False):
        """ Sort move lines according to Compassion criterias :
            Move line for current month at first,
            Then other move_lines, from the oldest to the newest.
        """
        # Propose up to 12 move lines for a complete year.
        if limit is not None and limit < 12:
            limit = 12

        res_asc = super(
            BankStatementLine, self).get_move_lines_for_reconciliation(
            excluded_ids, str, offset, limit, additional_domain,
            overlook_partner)

        # Sort results with date (current month at first)
        res_sorted = list()
        today = datetime.today().date()
        for mv_line in res_asc:
            mv_date = datetime.strptime(
                mv_line.date_maturity or mv_line.date, DF)
            if mv_date.month == today.month and mv_date.year == today.year:
                res_sorted.insert(0, mv_line.id)
            else:
                res_sorted.append(mv_line.id)

        # Put matching references at first
        # res_sorted = sorted(
        #     res_sorted, key=lambda mvl_data: mvl_data['ref'] == self.ref,
        #     reverse=True)
        return self.env['account.move.line'].browse(res_sorted)

    # @api.multi
    # def process_reconciliations(self, mv_line_dicts):
    #     """ Launch reconciliation in a job. """
    #     if self.env.context.get('async_mode', True):
    #         session = ConnectorSession.from_env(self.env)
    #         process_reconciliations_job.delay(
    #             session, self._name, self.ids, mv_line_dicts)
    #     else:
    #         self._process_reconciliations(mv_line_dicts)

    @api.model
    def product_id_changed(self, product_id, date):
        """ Called when a product is selected for counterpart.
        Returns useful info to fullfill other fields.
        """
        analytic_id = False
        account_id = self.env['product.product'].browse(
            product_id).property_account_income_id.id

        rule = self.env['account.analytic.default'].account_get(
            product_id, date=date)
        if rule:
            analytic_id = rule.analytic_id.id

        return {
            'analytic_id': analytic_id,
            'account_id': account_id
        }

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    # @api.multi
    # def _process_reconciliations(self, mv_line_dicts):
    #     super(BankStatementLine, self).process_reconciliations(
    #         mv_line_dicts)

    @api.multi
    def process_reconciliation(self, counterpart_aml_dicts=None,
                               payment_aml_rec=None, new_aml_dicts=None):
        """ Create invoice if product_id is set in move_lines
        to be created. """
        self.ensure_one()
        partner_invoices = dict()
        partner_inv_data = dict()
        old_counterparts = dict()
        if counterpart_aml_dicts is None:
            counterpart_aml_dicts = list()
        partner_id = self.partner_id.id
        counterparts = [data['move_line'] for data in counterpart_aml_dicts]
        counterparts = reduce(lambda m1, m2: m1 + m2.filtered('invoice_id'),
                              counterparts, self.env['account.move.line'])
        index = 0
        for mv_line_dict in new_aml_dicts:
            if mv_line_dict.get('product_id'):
                # Create invoice
                if partner_id in partner_inv_data:
                    partner_inv_data[partner_id].append(mv_line_dict)
                else:
                    partner_inv_data[partner_id] = [mv_line_dict]
                mv_line_dict['index'] = index

            index += 1
            if counterparts:
                # An invoice exists for that partner, we will use it
                # to put leftover amount in it, if any exists.
                invoice = counterparts[0].invoice_id
                partner_invoices[partner_id] = invoice
                old_counterparts[invoice.id] = counterparts[0]

        # Create invoice and update move_line_dicts to reconcile them.
        for partner_id, partner_data in partner_inv_data.iteritems():
            invoice = partner_invoices.get(partner_id)
            new_counterpart = self._create_invoice_from_mv_lines(
                partner_data, invoice)
            if invoice:
                # Remove new move lines
                for data in partner_data:
                    index = data.pop('index')
                    del new_aml_dicts[index]

                # Update old counterpart
                for counterpart_data in counterpart_aml_dicts:
                    if counterpart_data['move_line'] == \
                            old_counterparts[invoice.id]:
                        counterpart_data['move_line'] = new_counterpart
                        counterpart_data['credit'] = new_counterpart.debit
                        counterpart_data['debit'] = new_counterpart.credit
            else:
                # Add new counterpart and remove new move line
                for data in partner_data:
                    index = data.pop('index')
                    del new_aml_dicts[index]
                    data['move_line'] = new_counterpart
                    counterpart_aml_dicts.append(data)

        super(BankStatementLine, self).process_reconciliation(
            counterpart_aml_dicts, payment_aml_rec, new_aml_dicts)

    def _create_invoice_from_mv_lines(self, mv_line_dicts, invoice=None):
        # Generate a unique bvr_reference
        if self.ref and len(self.ref) == 27:
            ref = self.ref
        elif self.ref and len(self.ref) > 27:
            ref = mod10r(self.ref[:26])
        else:
            ref = mod10r((self.date.replace('-', '') + str(
                self.statement_id.id) + str(self.id)).ljust(26, '0'))

        if invoice:
            invoice.action_cancel()
            invoice.action_cancel_draft()
            invoice.write({'origin': self.statement_id.name})

        else:
            # Lookup for an existing open invoice matching the criterias
            invoices = self._find_open_invoice(mv_line_dicts)
            if invoices:
                # Get the bvr reference of the invoice or set it
                invoice = invoices[0]
                invoice.write({'origin': self.statement_id.name})
                if invoice.bvr_reference and not self.ref:
                    ref = invoice.bvr_reference
                else:
                    invoice.write({'bvr_reference': ref})
                self.write({
                    'ref': ref,
                    'invoice_id': invoice.id})
                return True

            # Setup a new invoice if no existing invoice is found
            journal_id = self.env['account.journal'].search(
                [('type', '=', 'sale')], limit=1).id
            if self.journal_id.code == 'BVR':
                payment_term_id = self.env.ref(
                    'sponsorship_switzerland.payment_term_bvr').id
            else:
                payment_term_id = self.env.ref(
                    'sponsorship_switzerland.payment_term_virement').id
            inv_data = {
                'account_id':
                    self.partner_id.property_account_receivable_id.id,
                'type': 'out_invoice',
                'partner_id': self.partner_id.id,
                'journal_id': journal_id,
                'date_invoice': self.date,
                'payment_term_id': payment_term_id,
                'bvr_reference': ref,
                'origin': self.statement_id.name,
                'comment': ';'.join(map(
                    lambda d: d.get('comment', ''),
                    mv_line_dicts))
            }
            invoice = self.env['account.invoice'].create(inv_data)

        for mv_line_dict in mv_line_dicts:
            product = self.env['product.product'].browse(
                mv_line_dict['product_id'])
            sponsorship_id = mv_line_dict.get('sponsorship_id')
            if not sponsorship_id:
                related_contracts = invoice.mapped(
                    'invoice_line_ids.contract_id')
                if related_contracts:
                    sponsorship_id = related_contracts[0].id
            contract = self.env['recurring.contract'].browse(sponsorship_id)
            if product.name == GIFT_NAMES[0] and contract and \
                    contract.child_id and contract.child_id.birthdate:
                invoice.date_invoice = self.env[
                    'generate.gift.wizard'].compute_date_birthday_invoice(
                    contract.child_id.birthdate, self.date)

            amount = mv_line_dict['credit']
            default_analytic = self.env[
                'account.analytic.default'].account_get(product.id,
                                                        self.partner_id.id)
            inv_line_data = {
                'name': self.name,
                'account_id': product.property_account_income_id.id,
                'price_unit': amount,
                'price_subtotal': amount,
                'contract_id': contract.id,
                'user_id': mv_line_dict.get('user_id'),
                'quantity': 1,
                'product_id': product.id,
                'partner_id': contract.partner_id.id if contract else
                self.partner_id.id,
                'invoice_id': invoice.id,
                # Remove analytic account from bank journal item:
                # it is only useful in the invoice journal item
                'account_analytic_id': mv_line_dict.pop(
                    'analytic_account_id',
                    default_analytic and default_analytic.analytic_id.id)
            }

            if product.categ_name in (
                    GIFT_CATEGORY, SPONSORSHIP_CATEGORY) and not contract:
                raise exceptions.UserError(_('Add a Sponsorship'))

            self.env['account.invoice.line'].create(inv_line_data)
            # Put payer as partner
            if contract:
                invoice.partner_id = contract.partner_id

        invoice.signal_workflow('invoice_open')
        self.ref = ref

        # Update move_lines data
        counterpart = invoice.move_id.line_ids.filtered(
            lambda ml: ml.debit > 0)
        return counterpart

    def _find_open_invoice(self, mv_line_dicts):
        """ Find an open invoice that matches the statement line and which
        could be reconciled with. """
        invoice_line_obj = self.env['account.invoice.line']
        inv_lines = invoice_line_obj
        for mv_line_dict in mv_line_dicts:
            amount = mv_line_dict['credit']
            inv_lines |= invoice_line_obj.search([
                ('partner_id', '=', mv_line_dict.get('partner_id')),
                ('state', 'in', ('open', 'draft')),
                ('product_id', '=', mv_line_dict.get('product_id')),
                ('price_subtotal', '=', amount)])

        return inv_lines.mapped('invoice_id').filtered(
            lambda i: i.amount_total == self.amount)


##############################################################################
#                            CONNECTOR METHODS                               #
##############################################################################
def related_action_reconciliations(session, job):
    line_ids = [arg[0] for arg in job.args[1]]
    statement_lines = session.env[job.args[0]].browse(line_ids)
    statement_ids = statement_lines.mapped('statement_id').ids
    action = {
        'name': _("Bank statements"),
        'type': 'ir.actions.act_window',
        'res_model': 'account.bank.statement',
        'view_type': 'form',
        'view_mode': 'form,tree',
        'res_id': statement_ids[0],
        'domain': [('id', 'in', statement_ids)],
    }
    return action


@job(default_channel='root.reconciliation')
@related_action(action=related_action_reconciliations)
def process_reconciliations_job(session, model_name, ids, mv_line_dicts):
    """Job for reconciling bank statment lines."""
    session.env[model_name].browse(ids)._process_reconciliations(mv_line_dicts)
