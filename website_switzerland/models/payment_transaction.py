##############################################################################
#
#    Copyright (C) 2024 Compassion CH (https://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#    @author: Noé Berdoz <nberdoz@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import models

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _post_process_after_done(self):
        """
        T1760 FIX wrong language in context coming from the payment process page
        Temporary fix for Odoo 14.0.
        Must be removed after the next migration if resolved in newer Odoo version.
        """
        # Core Odoo logs nothing per record here, so a hang in the
        # "Post process payment transactions" cron leaves no trace of which
        # transaction it stopped on.
        _logger.info("Post-processing payment transaction(s) %s", self.ids)
        available_langs = self.env["res.lang"].search([]).mapped("code")
        current_lang = self.env.lang or "de_DE"
        if current_lang not in available_langs:
            self = self.with_context(lang=None)
            for lang in available_langs:
                if lang.startswith(current_lang.split("_")[0]):
                    self = self.with_context(lang=lang)
                    break
        return super()._post_process_after_done()

    # T3374 diagnostics: the cron blocks for 120s somewhere inside
    # _post_process_after_done. These mark the entry of each step, so the last
    # line logged before the silence identifies it. Remove once diagnosed.
    def _check_amount_and_confirm_order(self):
        _logger.info("T3374 confirm order %s", self.sale_order_ids.ids)
        return super()._check_amount_and_confirm_order()

    def _invoice_sale_orders(self):
        _logger.info("T3374 invoice order %s", self.sale_order_ids.ids)
        return super()._invoice_sale_orders()
