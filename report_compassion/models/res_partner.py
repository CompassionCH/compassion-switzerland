##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import date, datetime
from babel.dates import format_date

from odoo import api, models, fields, _


class ResPartner(models.Model):
    """ Add fields for retrieving values for communications.
    """
    _inherit = 'res.partner'

    @api.multi
    def get_receipt_text(self, year):
        """ Formats the donation amount for the tax receipt. """
        return f'{self.get_receipt(year):,.2f}'\
            .replace('.00', '.-')\
            .replace(',', "'")

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
        """City and date displayed in the top right of a letter for Yverdon"""
        today = datetime.today()
        city = _("Yverdon-les-Bains")
        for partner in self:
            date = format_date(today, format='long', locale=partner.lang)
            formatted_date = f"le {date}" if 'fr' in partner.lang else date
            partner.date_communication = f"{city}, {formatted_date}"
