# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import api, models

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.multi
    def action_reset_password(self):
        create_mode = bool(self.env.context.get('create_user'))
        # Only override the rest behavior, not normal signup
        if create_mode:
            super(ResUsers, self).action_reset_password()
        else:
            config = self.env.ref(
                'partner_communication_switzerland.reset_password_email')
            for user in self:
                self.env['partner.communication.job'].create({
                    'partner_id': user.partner_id.id,
                    'config_id': config.id
                })

    @api.multi
    def _compute_signature_letter(self):
        """ Translate country in Signature (for Compassion Switzerland) """
        for user in self:
            employee = user.employee_ids
            signature = ''
            if len(employee) == 1:
                signature += employee.name + '<br/>'
                if employee.department_id:
                    signature += employee.department_id.name + '<br/>'
            signature += user.company_id.name.split(' ')[0] + ' '
            signature += user.company_id.country_id.name
            user.signature_letter = signature
