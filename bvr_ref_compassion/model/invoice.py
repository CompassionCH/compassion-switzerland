# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester <cyril.sester@outlook.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import logging

from openerp import models, fields, api
from openerp.tools import mod10r

logger = logging.getLogger(__name__)


class account_invoice(models.Model):

    ''' Inherit account.invoice in order to change BVR ref field type '''
    _inherit = "account.invoice"

    bvr_reference = fields.Char(
        "BVR REF.", size=32,
        track_visibility='onchange')

    @api.constrains('bvr_reference')
    def _check_bvr_ref(self):
        for data in self:
            if not data.bvr_reference:
                return True  # No check if no reference
            clean_ref = data.bvr_reference.replace(' ', '')
            if not clean_ref.isdigit() or len(clean_ref) > 27:
                raise exceptions.ValidationError('Error: BVR ref should only' +
                    'contain number (max. 27) and spaces.')
            clean_ref = clean_ref.rjust(27, '0')  # Add zeros to the left
            if not clean_ref == mod10r(clean_ref[0:26]):
                raise exceptions.ValidationError('Error: BVR ref should only' +
                    'contain number (max. 27) and spaces.')
        return True

class account_move_line(models.Model):
    _inherit = 'account.move.line'

    def get_bvr_ref(self, move_line_id):
        ''' Overload to take manual bvr ref if exists '''
        if isinstance(move_line_id, (tuple, list)):
            assert len(move_line_id) == 1, "Only 1 ID expected"
            move_line_id = move_line_id[0]

        move_line = self.browse(move_line_id)
        # We check if the type is bvr, if not we return false
        if move_line.invoice.bvr_reference:
            return move_line.invoice.bvr_reference
        else:
            bvr_ref = super(account_move_line, self).get_bvr_ref(move_line_id)
            move_line.invoice.write({'bvr_reference': bvr_ref})
            return bvr_ref


class account_move(models.Model):
    _inherit = 'account.move'

    def create(self, vals):
        invoice = self.env.context.get('invoice')
        if invoice and invoice.bvr_reference:
            vals['ref'] = invoice.bvr_reference
        return super(account_move, self).create(vals)
