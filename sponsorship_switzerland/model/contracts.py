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
from openerp.tools.translate import _


class contracts(orm.Model):
    _inherit = 'recurring.contract'

    def _get_gmc_states(self, cr, uid, context=None):
        """ Adds a new gmc state for tracking sponsorships for which we have
        to order the new picture of the child. """
        states = super(contracts, self)._get_gmc_states(cr, uid, context)
        states.insert(2, ('order_picture', _('Order picture')))
        return states

    def new_biennial(self, cr, uid, ids, context=None):
        """ Called when new picture and new case study is available. """
        self.write(cr, uid, ids, {'gmc_state': 'order_picture'}, context)
