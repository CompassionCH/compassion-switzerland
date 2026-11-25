from odoo import fields, models


class HrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    uuid = fields.Char(string="UUID", readonly=True)
