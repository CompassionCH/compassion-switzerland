# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.addons.thankyou_letters.models.res_partner import setlocale
from datetime import date, datetime

from odoo import api, models, fields, _


class ResPartner(models.Model):
    """ Add fields for retrieving values for communications.
    """
    _inherit = 'res.partner'

    @api.multi
    def get_receipt_text(self, year):
        """ Formats the donation amount for the tax receipt. """
        return '{:,.2f}'.format(self.get_receipt(year)).replace(
            '.00', '.-').replace(',', "'")

    @api.multi
    def get_receipt(self, year):
        """
        Return the amount paid from the partner in the given year
        :param year: int: year of selection
        :return: float: total amount
        """
        self.ensure_one()
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        invoice_lines = self.env['account.invoice.line'].search([
            ('last_payment', '>=', fields.Date.to_string(start_date)),
            ('last_payment', '<=', fields.Date.to_string(end_date)),
            ('state', '=', 'paid'),
            ('product_id.requires_thankyou', '=', True),
            '|', ('partner_id', '=', self.id),
            ('partner_id.parent_id', '=', self.id),
        ])
        return sum(invoice_lines.mapped('price_subtotal'))

    @api.multi
    def _compute_date_communication(self):
        lang_map = {
            'fr_CH': u'le %d %B %Y',
            'fr': u'le %d %B %Y',
            'de_DE': u'%d. %B %Y',
            'de_CH': u'%d. %B %Y',
            'en_US': u'%d %B %Y',
            'it_IT': u'%d %B %Y',
        }
        today = datetime.today()
        city = _("Yverdon-les-Bains")
        for partner in self:
            lang = partner.lang
            with setlocale(lang):
                date = today.strftime(
                    lang_map.get(lang, lang_map['en_US'])).decode('utf-8')
                partner.date_communication = city + u", " + date
