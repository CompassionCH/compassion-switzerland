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
