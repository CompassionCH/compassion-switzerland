##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.models import Model


class MyModel(Model):
    _inherit = 'account.payment.mode'

    def intersect(self, other):
        """ Utility to intersect from template """
        return self & other
