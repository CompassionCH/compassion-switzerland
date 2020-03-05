##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields


class SurveyUserInputLine(models.Model):
    _inherit = 'survey.user_input_line'

    partner_id = fields.Many2one(related='user_input_id.partner_id',
                                 store=True)
