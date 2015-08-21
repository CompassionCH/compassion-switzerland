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

from openerp.osv import orm, fields


class invoice_line(orm.Model):
    _inherit = 'account.invoice.line'

    _columns = {
        'child_name': fields.related(
            'contract_id', 'child_name', string='Child name', type='char')
    }
