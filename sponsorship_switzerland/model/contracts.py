# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.osv import orm
from openerp.tools.translate import _


class contracts(orm.Model):
    _inherit = 'recurring.contract'

    def _get_gmc_states(self, cr, uid, context=None):
        """ Adds a new gmc state for tracking sponsorships for which we have
        to order the new picture of the child. Remove 'casestudy' and
        'picture' states which are useless for Switzerland."""
        return [
            ('order_picture', _('Order Picture')),
            ('biennial', _('Biennial')),
            ('depart', _('Child Departed')),
            ('transfer', _('Child Transfer'))]

    def new_biennial(self, cr, uid, ids, context=None):
        """ Called when new picture and new case study is available. """
        self.write(cr, uid, ids, {'gmc_state': 'order_picture'}, context)

    def set_gmc_event(self, cr, uid, ids, event, context=None):
        """
        Called when a Child Update was received for a sponsored child.
        Arg event can have one of the following values :
            - Transfer : child was transferred to another project
            - CaseStudy : child has a new casestudy
            - NewImage : child has a new image

        We handle only the Transfer event, as other events are not relevant
        for Switzerland.
        """
        if event == 'Transfer':
            return self.write(cr, uid, ids, {'gmc_state': event.lower()},
                              context)
        return True

    # Called only at module installation
    def migrate_contracts(self, cr, uid, context=None):
        """ Remove no more used gmc_states. """
        cr.execute("""
            UPDATE recurring_contract SET gmc_state = NULL
            WHERE gmc_state IN ('picture', 'casestudy')
        """)
        return True

    def _cancel_confirm_invoices(self, cr, uid, cancel_ids, confirm_ids,
                                 context=None, keep_lines=None):
        """ For LSV/DD contracts, free the invoices before cancelling them.
        """
        if context is None:
            ctx = dict()
        else:
            ctx = context.copy()
        inv_obj = self.pool.get('account.invoice')
        ctx['active_ids'] = cancel_ids
        try:
            order_id = inv_obj.cancel_payment_lines(cr, uid, cancel_ids, ctx)
            order_obj = self.pool.get('payment.order')
            order_obj.unlink(cr, uid, order_id, context)
            # I don't know why payment lines are not automatically deleted...
            payment_line_obj = self.pool.get('payment.line')
            line_ids = payment_line_obj.search(cr, uid, [
                ('order_id', '=', order_id)], context=context)
            payment_line_obj.unlink(cr, uid, line_ids, context)
        except orm.except_orm:  # An error is raised if no invoice was to free
            pass
        super(contracts, self)._cancel_confirm_invoices(
            cr, uid, cancel_ids, confirm_ids, context, keep_lines)

    def _on_sponsorship_finished(self, cr, uid, ids, context=None):
        """ When a sponsorship is terminated, we clean ALL open invoices
        because we don't want to ask the sponsor to pay what is still due.
        """
        super(contracts, self)._on_sponsorship_finished(cr, uid, ids, context)
        for sponsorship in self.browse(cr, uid, ids, context):
            sponsorship.clean_invoices(since_date=sponsorship.start_date,
                                       to_date=sponsorship.end_date,
                                       clean_invoices_paid=False)
