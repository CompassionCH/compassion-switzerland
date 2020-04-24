##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, api


class CrowdfundingProjectSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    notified_employee_ids = fields.Many2many(
        "hr.employee", string="Employees notified when projects are created")

    @api.model
    def get_values(self):
        res = super().get_values()
        config = self.env["ir.config_parameter"].sudo()
        res['notified_employee_ids'] = config.get_param("notified_employee_ids")
        return res

    @api.multi
    def set_values(self):
        super().set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'notified_employee_ids', self.notified_employee_ids
        )
