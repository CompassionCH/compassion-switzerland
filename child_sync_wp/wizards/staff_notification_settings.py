# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import api, models, fields


class StaffNotificationSettings(models.TransientModel):
    """ Settings configuration for any Notifications."""
    _inherit = 'staff.notification.settings'

    # Users to notify when new Sponsorship is made
    sponsorship_fr_id = fields.Many2one(
        'res.partner', 'New sponsorships (FR)',
        domain=[
            ('user_ids', '!=', False),
            ('user_ids.share', '=', False),
        ])
    sponsorship_de_id = fields.Many2one(
        'res.partner', 'New sponsorships (DE)',
        domain=[
            ('user_ids', '!=', False),
            ('user_ids.share', '=', False),
        ])
    sponsorship_it_id = fields.Many2one(
        'res.partner', 'New sponsorships (IT)',
        domain=[
            ('user_ids', '!=', False),
            ('user_ids.share', '=', False),
        ])

    @api.multi
    def set_sponsorship_fr_id(self):
        self.env['ir.config_parameter'].set_param(
            'child_wp.sponsorship_notify_fr_id',
            str(self.sponsorship_fr_id.id)
        )

    @api.multi
    def set_sponsorship_de_id(self):
        self.env['ir.config_parameter'].set_param(
            'child_wp.sponsorship_notify_de_id',
            str(self.sponsorship_de_id.id)
        )

    @api.multi
    def set_sponsorship_it_id(self):
        self.env['ir.config_parameter'].set_param(
            'child_wp.sponsorship_notify_it_id',
            str(self.sponsorship_it_id.id)
        )

    @api.model
    def get_default_values(self, _fields):
        param_obj = self.env['ir.config_parameter']
        res = {
            'sponsorship_fr_id': int(param_obj.get_param(
                'child_wp.sponsorship_fr_id', '18001')),
            'sponsorship_de_id': int(param_obj.get_param(
                'child_wp.sponsorship_de_id', '18001')),
            'sponsorship_it_id': int(param_obj.get_param(
                'child_wp.sponsorship_it_id', '18002')),
        }
        res.update(super(StaffNotificationSettings,
                         self).get_default_values(_fields))
        return res
