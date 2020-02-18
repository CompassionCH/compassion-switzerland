##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields
from odoo.tools import mod10r
from odoo.addons.sponsorship_compassion.models.product_names import GIFT_REF

import logging

logger = logging.getLogger(__name__)


class GenerateGiftWizard(models.TransientModel):
    """ This wizard generates a Gift Invoice for a given contract. """
    _inherit = 'generate.gift.wizard'

    @api.multi
    def _setup_invoice(self, contract, invoice_date):
        res = super()._setup_invoice(contract, invoice_date)
        res['reference'] = self.generate_bvr_reference(
            contract, self.product_id)
        self._maybe_update_date_for_lsv_dd(res)
        return res

    @api.model
    def _maybe_update_date_for_lsv_dd(self, res):
        """ Invoices for gift should be set at the beginning of the month to be
        processed together with the sponsorship for the month."""
        payment_mode_id = res['payment_mode_id']
        lsv = self.env.ref('sponsorship_switzerland.payment_mode_lsv').ids
        dd = self.env.ref(
            'sponsorship_switzerland.payment_mode_postfinance_dd').ids
        if payment_mode_id in lsv + dd:
            date_invoice = fields.Date.from_string(res['date_invoice'])
            start_of_month = date_invoice.replace(day=1)
            res['date_invoice'] = fields.Date.to_string(start_of_month)

    @api.model
    def generate_bvr_reference(self, contract, product):
        product = product.with_context(lang='en_US')
        ref = contract.gift_partner_id.ref
        bvr_reference = '0' * (9 + (7 - len(ref))) + ref
        commitment_number = str(contract.commitment_number)
        bvr_reference += '0' * (5 - len(commitment_number)) + commitment_number
        # Type of gift
        bvr_reference += str(GIFT_REF.index(product.default_code) + 1)
        bvr_reference += '0' * 4

        if contract.payment_mode_id and 'LSV' in contract.payment_mode_id.name:
            # Get company BVR adherent number
            user = self.env.user
            bank_obj = self.env['res.partner.bank']
            company_bank = bank_obj.search([
                ('partner_id', '=', user.company_id.partner_id.id),
                ('lsv_identifier', '!=', False)])
            if company_bank:
                bvr_reference = company_bank.bvr_adherent_num + \
                    bvr_reference[9:]
        if len(bvr_reference) == 26:
            return mod10r(bvr_reference)

        return False
