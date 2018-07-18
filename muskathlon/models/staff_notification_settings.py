# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
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

    # Users to notify for Muskathlon Registration
    muskathlon_lead_notify_id = fields.Many2one(
        'res.users', 'Muskathlon Registrations',
        domain=[('share', '=', False)]
    )
    muskathlon_order_notify_id = fields.Many2one(
        'res.users', 'Muskathlon Material Orders',
        domain=[('share', '=', False)]
    )

    @api.multi
    def set_muskathlon_lead_notify_ids(self):
        self.env['ir.config_parameter'].set_param(
            'muskathlon.muskathlon_lead_notify_id',
            str(self.muskathlon_lead_notify_id.id)
        )

    @api.multi
    def set_muskathlon_order_notify_id(self):
        self.env['ir.config_parameter'].set_param(
            'muskathlon.muskathlon_order_notify_id',
            str(self.muskathlon_order_notify_id.id)
        )

    @api.model
    def get_default_values(self, _fields):
        res = super(StaffNotificationSettings,
                    self).get_default_values(_fields)
        param_obj = self.env['ir.config_parameter']
        res['muskathlon_lead_notify_id'] = int(param_obj.get_param(
            'muskathlon.muskathlon_lead_notify_id', 1))
        res['muskathlon_order_notify_id'] = int(param_obj.get_param(
            'muskathlon.muskathlon_order_notify_id', 1))
        return res
