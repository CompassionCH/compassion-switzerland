# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Samuel Fringeli <samuel.fringeli@me.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields


class StaffNotificationSettings(models.TransientModel):
    """ Settings configuration for any Notifications."""
    _inherit = 'staff.notification.settings'

    # Users to notify after Disaster Alert
    invalid_mail_notify_ids = fields.Many2many(
        'res.partner', string='Invalid mail ids',
        domain=[
            ('user_ids', '!=', False),
            ('user_ids.share', '=', False),
        ]
    )

    @api.multi
    def set_invalid_mail_notify_ids(self):
        self.env['ir.config_parameter'].set_param(
            'partner_communication_switzerland.invalid_mail_notify_ids',
            ','.join(map(str, self.invalid_mail_notify_ids.ids)))

    @api.model
    def get_default_values(self, _fields):
        param_obj = self.env['ir.config_parameter']
        res = {'invalid_mail_notify_ids': False}
        partners = param_obj.get_param(
            'partner_communication_switzerland.invalid_mail_notify_ids', False)
        if partners:
            res['invalid_mail_notify_ids'] = map(int, partners.split(','))
        return res

    @api.model
    def get_param(self, param):
        """ Retrieve a single parameter. """
        return self.get_default_values([param])[param]
