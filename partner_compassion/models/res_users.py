from odoo import models, fields

class ResUsers(models.Model):

    _inherit = "res.users"

    partner_id = fields.Many2one(ondelete='cascade')
