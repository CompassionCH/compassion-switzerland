
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
    _inherit = 'res.config.settings'

    # Notify for advocate birthdays
    advocate_birthday_fr_id = fields.Many2one(
        'res.partner', 'Advocate birthday (FR)',
        domain=[
            ('user_ids', '!=', False),
            ('user_ids.share', '=', False),
        ])
    advocate_birthday_de_id = fields.Many2one(
        'res.partner', 'Advocate birthday (DE)',
        domain=[
            ('user_ids', '!=', False),
            ('user_ids.share', '=', False),
        ])
    advocate_birthday_it_id = fields.Many2one(
        'res.partner', 'Advocate birthday (IT)',
        domain=[
            ('user_ids', '!=', False),
            ('user_ids.share', '=', False),
        ])
    advocate_birthday_en_id = fields.Many2one(
        'res.partner', 'Advocate birthday (EN)',
        domain=[
            ('user_ids', '!=', False),
            ('user_ids.share', '=', False),
        ])

    @api.multi
    def set_advocate_birthday_fr(self):
        self.env['ir.config_parameter'].set_param(
            'partner_compassion.advocate_birthday_fr_id',
            str(self.advocate_birthday_fr_id.id)
        )

    @api.multi
    def set_advocate_birthday_de(self):
        self.env['ir.config_parameter'].set_param(
            'partner_compassion.advocate_birthday_de_id',
            str(self.advocate_birthday_de_id.id)
        )

    @api.multi
    def set_advocate_birthday_it(self):
        self.env['ir.config_parameter'].set_param(
            'partner_compassion.advocate_birthday_it_id',
            str(self.advocate_birthday_it_id.id)
        )

    @api.multi
    def set_advocate_birthday_en(self):
        self.env['ir.config_parameter'].set_param(
            'partner_compassion.advocate_birthday_en_id',
            str(self.advocate_birthday_en_id.id)
        )

    @api.multi
    def set_values(self):
        super().set_values()
        self.set_advocate_birthday_de()
        self.set_advocate_birthday_en()
        self.set_advocate_birthday_fr()
        self.set_advocate_birthday_it()

    @api.model
    def get_values(self):
        res = super().get_values()
        return res

    @api.model
    def get_default_values(self, _fields):
        res = super().get_default_values(_fields)
        param_obj = self.env['ir.config_parameter']
        res.update({
            'advocate_birthday_fr_id': int(param_obj.get_param(
                'partner_compassion.advocate_birthday_fr_id', 0)),
            'advocate_birthday_de_id': int(param_obj.get_param(
                'partner_compassion.advocate_birthday_de_id', 0)),
            'advocate_birthday_it_id': int(param_obj.get_param(
                'partner_compassion.advocate_birthday_it_id', 0)),
            'advocate_birthday_en_id': int(param_obj.get_param(
                'partner_compassion.advocate_birthday_en_id', 0)),
        })
        return res
