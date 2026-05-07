from uuid import uuid4

from odoo import api, fields, models


class Employee(models.Model):
    _inherit = "hr.employee"

    uuid = fields.Char(string="UUID", copy=False)

    _sql_constraints = [
        ("uuid_unique", "UNIQUE (uuid)", "uuid should be unique"),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals.setdefault("uuid", str(uuid4()))
        return super().create(vals_list)
