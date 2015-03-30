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
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF

from . import gp_connector
from datetime import datetime


class child_compassion(orm.Model):
    _inherit = 'compassion.child'

    def write(self, cr, uid, ids, vals, context=None):
        """Update GP with the last information of the child."""
        res = super(child_compassion, self).write(cr, uid, ids, vals, context)
        if not isinstance(ids, list):
            ids = [ids]
        gp_connect = gp_connector.GPConnect()

        for child in self.browse(cr, uid, ids, context):
            if 'state' in vals:
                gp_connect.set_child_sponsor_state(child)
            if 'code' in vals:
                # Update the Sponsorships related to this child in GP
                con_obj = self.pool.get('recurring.contract')
                con_ids = con_obj.search(
                    cr, uid, [('child_id', '=', child.id)], context=context)
                if con_ids:
                    gp_connect.update_child_sponsorship(child.code, con_ids)

        return res


class child_property(orm.Model):
    """ Upsert Case Studies """
    _inherit = 'compassion.child.property'

    def attach_pictures(self, cr, uid, ids, pictures_id, context=None):
        """ Don't put contract in biennial state if biennial is more
            recent than cs. """
        gp_connect = gp_connector.GPConnect()
        res = super(child_property, self).attach_pictures(
            cr, uid, ids, pictures_id, context)
        if not isinstance(ids, list):
            ids = [ids]

        case_study = self.browse(cr, uid, ids, context)[0]
        for contract in case_study.child_id.contract_ids:
            last_biennial = gp_connect.get_last_biennial(contract)
            if last_biennial and last_biennial >= datetime.strptime(
                    case_study.info_date, DF).date():
                contract.write({'gmc_state': False})

        return res
