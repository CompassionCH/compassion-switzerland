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

from . import gp_connector


class ChildCompassion(orm.Model):
    _inherit = 'compassion.child'

    def write(self, cr, uid, ids, vals, context=None):
        """Update GP with the last information of the child."""
        res = super(ChildCompassion, self).write(cr, uid, ids, vals, context)
        if not isinstance(ids, list):
            ids = [ids]
        gp_connect = gp_connector.GPConnect()

        for child in self.browse(cr, uid, ids, context):
            if 'state' in vals or 'active' in vals:
                gp_connect.set_child_sponsor_state(child)
            if 'local_id' in vals:
                # Update the Sponsorships related to this child in GP
                con_obj = self.pool.get('recurring.contract')
                con_ids = con_obj.search(
                    cr, uid, [('child_id', '=', child.id)], context=context)
                if con_ids:
                    gp_connect.update_child_sponsorship(child.local_id,
                                                        con_ids)

        return res
