##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#    modification: Samy Bucher <samy.bucher@outlook.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models


class Gift(models.Model):
    _inherit = "sponsorship.gift"

    letter_id = fields.Many2one("correspondence", "Thank you letter", readonly=False)
