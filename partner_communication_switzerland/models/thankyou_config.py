##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models


class ThankYouConfig(models.Model):
    _inherit = "thankyou.config"

    @api.multi
    def for_donation(self, invoice_lines):
        # Special case for legacy donation : always treat as large donation
        if "legacy" in invoice_lines.with_context(lang="en_US").mapped(
                "product_id.name"
        ):
            # Will return the largest donation configuration
            return self.sorted()[-1]
        return super().for_donation(invoice_lines)

    def build_inform_mode(self, partner, print_if_not_email=False):
        """ Returns how the partner should be informed for the given
        thank you letter (digital, physical or False).
        It makes the product of the thank you preference and the partner
        :returns: send_mode (physical/digital/False), auto_mode (True/False)
        """
        return self.env["partner.communication.config"].build_inform_mode(
            partner,
            self.send_mode,
            print_if_not_email=print_if_not_email,
            send_mode_pref_field="thankyou_preference",
        )
