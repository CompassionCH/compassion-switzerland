# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp.addons.sponsorship_compassion.models.product import GIFT_NAMES
from openerp import api, models, _


class Contract(models.Model):
    _inherit = 'recurring.contract'

    @api.multi
    def get_gift_communication(self, product):
        self.ensure_one()
        child = self.child_id.with_context(lang=self.partner_id.lang)
        communication = u"{firstname} ({local_id})<br/>{product}<br/>" \
                        u"{birthdate}"
        vals = {
            'firstname': child.firstname,
            'local_id': child.local_id,
            'product': product.with_context(lang=self.partner_id.lang).name,
            'birthdate': _('Born in') + ' ' + child.birthdate
        }
        return communication.format(**vals)

    @api.multi
    def generate_bvr_reference(self, product):
        self.ensure_one()
        return self.env['generate.gift.wizard'].generate_bvr_reference(
            self, product)

    @api.model
    def get_sponsorship_gift_products(self):
        return self.env['product.product'].with_context(lang='en_US').search([
            ('name', 'in', GIFT_NAMES[:3])])
