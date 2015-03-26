# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Coninckx <david@coninckx.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp.osv import orm
from ..model.sync_typo3 import Sync_typo3


class delegate_child_wizard(orm.TransientModel):
    _inherit = 'delegate.child.wizard'

    def delegate(self, cr, uid, ids, context=None):
        child_ids = self._default_child_ids(cr, uid, context)
        child_obj = self.pool.get('compassion.child')

        typo3_to_remove_ids = list()
        for child in child_obj.browse(cr, uid, child_ids, context):
            if (child.state == 'I'):
                typo3_to_remove_ids.append(child.id)
        res = True
        if typo3_to_remove_ids:
            res = child_obj.child_remove_from_typo3(
                cr, uid, typo3_to_remove_ids, context)

        res = super(delegate_child_wizard, self).delegate(
            cr, uid, ids, context) and res

        return res or Sync_typo3.typo3_index_error(cr, uid, self, context)
