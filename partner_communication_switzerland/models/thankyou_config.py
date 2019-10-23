# -*- coding: utf-8 -*-
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
    _inherit = 'thankyou.config'

    @api.multi
    def for_donation(self, invoice_lines):
        # Special case for legacy donation : always treat as large donation
        if 'legacy' in invoice_lines.with_context(lang='en_US').mapped(
                'product_id.name'):
            # Will return the largest donation configuration
            return self.sorted()[-1]
        return super(ThankYouConfig, self).for_donation(invoice_lines)
