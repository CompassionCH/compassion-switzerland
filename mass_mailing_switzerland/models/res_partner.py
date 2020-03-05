##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, api, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    date_opt_out = fields.Date()

    @api.model
    def create(self, vals):
        if vals.get('opt_out'):
            vals['date_opt_out'] = fields.Date.today()
        return super().create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('opt_out'):
            vals['date_opt_out'] = fields.Date.today()
        elif 'opt_out' in vals:
            vals['date_opt_out'] = False
        return super().write(vals)
