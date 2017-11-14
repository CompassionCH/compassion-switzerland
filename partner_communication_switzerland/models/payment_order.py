from odoo.models import Model


class MyModel(Model):
    _inherit = 'account.payment.mode'

    def intersect(self, other):
        """ Utility to intersect from template """
        return self & other
