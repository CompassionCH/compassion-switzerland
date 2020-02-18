##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Samy Bucher <samy.bucher@outlook.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models
from odoo import fields


class Correspondence(models.Model):
    _inherit = 'correspondence'

    gift_id = fields.Many2one('sponsorship.gift', 'Gift')
