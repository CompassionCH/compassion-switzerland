from odoo import models


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _post_process_after_done(self):
        # T1760 FIX wrong language in context coming from the payment process page
        available_langs = self.env["res.lang"].search([]).mapped("code")
        if self.env.lang not in available_langs:
            self = self.with_context(lang=None)
            for lang in available_langs:
                if lang.startswith(self.env.lang.split("_")[0]):
                    self = self.with_context(lang=lang)
                    break
        return super()._post_process_after_done()
