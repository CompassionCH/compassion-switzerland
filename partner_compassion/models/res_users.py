from odoo import models, fields


class ResUsers(models.Model):

    _inherit = "res.users"

    partner_id = fields.Many2one(ondelete='cascade')

    def write(self, vals):
        # Avoid cascading the name from the user
        return super(ResUsers, self.with_context(write_from_user=True)).write(vals)
