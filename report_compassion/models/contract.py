# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields


class AccountInvoice(models.Model):
    """
    Make Invoice translatable for communications with dates.
    """
    _inherit = ['account.invoice', 'translatable.model']
    _name = 'account.invoice'

    # Gender field is mandatory for translatable models
    gender = fields.Char(compute='_compute_gender')

    def _compute_gender(self):
        for i in self:
            i.gender = 'M'


class Contract(models.Model):
    _inherit = 'recurring.contract'

    @api.multi
    def get_gift_communication(self, product):
        self.ensure_one()
        lang = self.partner_id.lang
        child = self.child_id.with_context(lang=lang)
        born = {
            'en_US': u'Born in',
            'fr_CH': u'Né le',
            'de_DE': u'Geburtstag',
            'it_IT': u'Compleanno',
        }
        communication = u"{firstname} ({local_id})<br/>{product}<br/>" \
                        u"{birthdate}"
        birthdate = fields.Date.from_string(child.birthdate).strftime(
            "%d.%m.%Y")
        vals = {
            'firstname': child.preferred_name,
            'local_id': child.local_id,
            'product': product.with_context(lang=lang).name,
            'birthdate': born[lang] + ' ' + birthdate
            if 'Birthday' in product.name else ''
        }
        return communication.format(**vals)

    @api.multi
    def generate_bvr_reference(self, product):
        self.ensure_one()
        return self.env['l10n_ch.payment_slip']._space(self.env[
            'generate.gift.wizard'].generate_bvr_reference(
            self, product).lstrip('0'))

    @api.model
    def get_sponsorship_gift_products(self):
        gift_categ_id = self.env.ref(
            'sponsorship_compassion.product_category_gift').id
        return self.env['product.product'].search([
            ('categ_id', '=', gift_categ_id)])
