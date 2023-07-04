##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    @author: Théo Nikles <theo.nikles@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields


class MailActivity(models.Model):
    _inherit = "mail.activity"

    # Override domain to consider only internal users
    user_id = fields.Many2one(domain="[('share', '=', False)]")
