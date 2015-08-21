# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Copyright EduSense BV, Therp BV
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import models, fields


class payment_mode(models.Model):
    _inherit = "payment.mode"

    payment_term_ids = fields.Many2many(
        'account.payment.term', 'account_payment_order_terms_rel',
        'mode_id', 'term_id', 'Payment terms',
        help='Limit selected invoices to invoices with these payment terms'
    )
