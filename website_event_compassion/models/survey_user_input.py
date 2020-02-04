##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging

from odoo import api, models
logger = logging.getLogger(__name__)


class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    @api.multi
    def write(self, vals):
        """
        Update event registration if any is linked to the medical survey.
        """
        res = super().write(vals)
        if vals.get('state') == 'done':
            medical_registrations = self.env['event.registration'].search([
                ('medical_survey_id', 'in', self.ids)
            ])
            needs_discharge = medical_registrations.filtered(
                'requires_medical_discharge')
            discharge_ok = medical_registrations - needs_discharge
            needs_discharge.send_medical_discharge()
            discharge_ok.skip_medical_discharge()
        return res
