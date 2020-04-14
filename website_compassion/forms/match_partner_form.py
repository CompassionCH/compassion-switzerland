##############################################################################
#
#    Copyright (C) 2018-2020 Compassion CH (http://www.compassion.ch)
#    @author: Maxime Beck
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models


class PartnerMatchform(models.AbstractModel):
    _inherit = "cms.form.match.partner"

    def form_before_create_or_update(self, values, extra_values):
        """
        Avoid updating partner at GMC, use context to prevent this.
        """
        super(
            PartnerMatchform, self.with_context(no_upsert=True)
        ).form_before_create_or_update(values, extra_values)
