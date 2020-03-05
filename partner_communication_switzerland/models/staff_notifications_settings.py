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
    _inherit = 'res.config.settings'

    # Users to notify after Disaster Alert
    invalid_mail_notify_ids = fields.Many2many(
        comodel_name='res.partner', string='Invalid mail',
        relation='invalid_mail_staff_notify_rel',
        column1='staff_id', column2='partner_id',
        domain=[
            ('user_ids', '!=', False),
            ('user_ids.share', '=', False),
        ]
    )

    @api.multi
    def set_invalid_mail_notify_ids(self):
        self.env['ir.config_parameter'].set_param(
            'partner_communication_switzerland.invalid_mail_notify_ids',
            ','.join(list(map(str, self.invalid_mail_notify_ids.ids))))

    @api.multi
    def set_values(self):
        super().set_values()
        self.set_invalid_mail_notify_ids()

    @api.model
    def get_values(self):
        param_obj = self.env['ir.config_parameter'].sudo()
        res = super().get_values()
        res['invalid_mail_notify_ids'] = False
        partners = param_obj.get_param(
            'partner_communication_switzerland.invalid_mail_notify_ids', False)
        if partners:
            res['invalid_mail_notify_ids'] = list(map(int, partners.split(',')))
        return res
