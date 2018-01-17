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
from datetime import date

from odoo import api, models, fields


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
        move_lines = self.env['account.move.line'].search([
            ('partner_id', '=', self.id),
            ('date', '>=', fields.Date.to_string(start_date)),
            ('date', '<=', fields.Date.to_string(end_date)),
            ('account_id.code', '=', '1050'),
            ('journal_id.code', '=', 'SAJ'),
            ('debit', '>', 0)
        ])
        return sum(move_lines.mapped('debit'))
