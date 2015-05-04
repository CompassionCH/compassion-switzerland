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


class child_depart_wizard(orm.TransientModel):
    _inherit = 'child.depart.wizard'

    def child_depart(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context)
        child = wizard.child_id

        res = True
        if child.state == 'I':
            res = child.child_remove_from_typo3()

        res = super(child_depart_wizard, self).child_depart(
            cr, uid, ids, context) and res

        return res or Sync_typo3.typo3_index_error(cr, uid, self, context)
