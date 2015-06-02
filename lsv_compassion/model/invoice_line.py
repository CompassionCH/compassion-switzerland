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

    def _get_child_name(self, cr, uid, ids, name, dict, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context):
            child_name = ''
            if line.contract_id and line.contract_id.child_id:
                child_name = line.contract_id.child_id.name
            res[line.id] = child_name

        return res

    _columns = {
        'child_name': fields.function(
            _get_child_name, string='Child name', type='char')
    }
