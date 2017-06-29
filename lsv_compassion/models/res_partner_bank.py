# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from odoo import models, api


class PartnerBank(models.Model):
    _inherit = "res.partner.bank"

    @api.model
    def convert_ccp_iban(self):
        """
        Utility for migration to v9.
        See https://fr.wikipedia.org/wiki/International_Bank_Account_Number
        """
        control_ch = '121700'
        postfinance = '09000000'
        for bank in self.search([
            ('bank_id.bic', '=', 'POFICHBEXXX'),
            ('acc_type', '=', 'bank')
        ]):
            ccp_parts = bank.acc_number.split('-')
            account = postfinance + ccp_parts[0] + ccp_parts[1].rjust(
                6, '0') + ccp_parts[2]
            control = account + control_ch
            mod_17 = str(98 - (int(control) % 97)).rjust(2, '0')
            bank.acc_number = 'CH' + mod_17 + account
