#    Copyright (C) 2019 Compassion CH
#    @author: Stephane Eicher <seicher@compassion.ch>


from odoo import models, api


class Phonecall(models.Model):
    _inherit = "crm.phonecall"

    @api.multi
    def write(self, values):
        # Remove default value for the field state in context to avoid
        # mail.mail to use it.
        return super(Phonecall, self.with_context(default_state=False)).write(values)
