# -*- coding: utf-8 -*-45.00
# Copyright (C) 2019 Compassion CH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from email.utils import parseaddr
from odoo import api, models


class CrmClaim(models.Model):
    _inherit = "crm.claim"

    @api.multi
    def write(self, values):
        """
        - Create alias with the e-mail address if a partner is selected.
        """
        super(CrmClaim, self).write(values)
        if values.get('partner_id'):
            partner = self.env['res.partner'].browse(values['partner_id'])
            for request in self:
                email_alias = parseaddr(request.email_from)[1]
                if email_alias != partner.email:
                    partner.with_context(no_upsert=True).copy({
                        'type': 'email_alias',
                        'email': email_alias,
                        'contact_id': partner.id,
                        'active': False,
                    })
        return True
