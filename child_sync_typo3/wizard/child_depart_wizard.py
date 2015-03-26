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
from openerp.osv import orm
from ..model.sync_typo3 import Sync_typo3


class end_sponsorship_wizard(orm.TransientModel):
    _inherit = 'end.sponsorship.wizard'

    def child_depart(self, cr, uid, ids, context=None):
        res = super(end_sponsorship_wizard, self).child_depart(
            cr, uid, ids, context)

        wizard = self.browse(cr, uid, ids[0], context)
        child = wizard.child_id
        vals = {'exit_date': wizard.end_date,
                'state': 'F'}

        if child.state == 'I':
            res = child.child_remove_from_typo3()
        child.write(vals)

        return res or Sync_typo3.typo3_index_error(cr, uid, self, context)
