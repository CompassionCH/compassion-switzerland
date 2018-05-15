# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields


class StaffNotificationSettings(models.TransientModel):
    """ Settings configuration for any Notifications."""
    _inherit = 'staff.notification.settings'

    # Users to notify after Disaster Alert
    muskathlon_lead_notify_ids = fields.Many2many(
        'res.users', 'staff_muskathlon_notification_ids',
        'config_id', 'partner_id',
        string='Muskathlon Registrations',
        domain=[('share', '=', False)]
    )

    @api.multi
    def set_muskathlon_lead_notify_ids(self):
        self.env['ir.config_parameter'].set_param(
            'muskathlon.muskathlon_lead_notify_ids',
            ','.join(map(str, self.muskathlon_lead_notify_ids.ids)))

    @api.model
    def get_default_values(self, _fields):
        res = super(StaffNotificationSettings,
                    self).get_default_values(_fields)
        param_obj = self.env['ir.config_parameter']
        partners = param_obj.get_param(
            'muskathlon.muskathlon_lead_notify_ids', False)
        if partners:
            res['muskathlon_lead_notify_ids'] = map(int, partners.split(','))
        return res
