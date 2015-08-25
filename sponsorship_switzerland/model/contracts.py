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

from openerp import api, exceptions, models, _


class contracts(models.Model):
    _inherit = 'recurring.contract'

    @api.model
    def _get_gmc_states(self):
        """ Adds a new gmc state for tracking sponsorships for which we have
        to order the new picture of the child. Remove 'casestudy' and
        'picture' states which are useless for Switzerland."""
        return [
            ('order_picture', _('Order Picture')),
            ('biennial', _('Biennial')),
            ('depart', _('Child Departed')),
            ('transfer', _('Child Transfer'))]

    @api.multi
    def new_biennial(self):
        """ Called when new picture and new case study is available. """
        self.write({'gmc_state': 'order_picture'})

    @api.multi
    def set_gmc_event(self, event):
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
            return self.write({'gmc_state': event.lower()})
        return True

    @api.multi
    def button_reset_gmc_state(self, value):
        """ Button called from Kanban view on all contracts of one group. """

        contracts = self.env['recurring.contract'].search([
            ('gmc_state', '=', value)])
        return contracts.reset_gmc_state()

    @api.multi
    def reset_gmc_state(self):
        """ Useful for manually unset GMC State. """
        return self.write({'gmc_state': False})

    # Called only at module installation
    @api.model
    def migrate_contracts(self):
        """ Remove no more used gmc_states. """
        self.env.cr.execute("""
            UPDATE recurring_contract SET gmc_state = NULL
            WHERE gmc_state IN ('picture', 'casestudy')
        """)
        self.env.invalidate_all()
        return True

    @api.multi
    def _cancel_confirm_invoices(self, invoice_cancel, invoice_confirm,
                                 keep_lines=None):
        """ For LSV/DD contracts, free the invoices before cancelling them.
        """
        self.env.context = self.with_context(
            active_id=invoice_cancel.ids).env.context
        try:
            order = invoice_cancel.cancel_payment_lines()
            order_id = order.id
            order.unlink()
            # I don't know why payment lines are not automatically deleted...
            lines = self.env['payment.line'].search([
                ('order_id', '=', order_id)])
            lines.unlink()
        # An error is raised if no invoice was to free
        except exceptions.Warning:
            super(contracts, self)._cancel_confirm_invoices(
            invoice_cancel, invoice_confirm, keep_lines)
        super(contracts, self)._cancel_confirm_invoices(
            invoice_cancel, invoice_confirm, keep_lines)
