#    Copyright (C) 2020 Compassion CH
#    @author: Quentin Gigon

from odoo import models, fields


class Website(models.Model):
    _inherit = "website"

    theme_id = fields.Many2one(
        "theme.ir.ui.view", "Website theme")
