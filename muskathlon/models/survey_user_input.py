##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, api


class SurveyUserInput(models.Model):
    _name = 'survey.user_input'

    _inherit = ['survey.user_input', 'mail.template']

    @api.multi
    def write(self, vals):
        """
        Automatically complete Medical Survey task when user filled it
        """
        res = super(SurveyUserInput, self).write(vals)
        if vals.get('state') == 'done':
            # Search for Muskathlon medical surveys
            registrations = self.env['event.registration'].sudo().search([
                ('partner_id', 'in', self.mapped('partner_id').ids),
                ('event_id.event_type_id', '=', self.env.ref(
                    'muskathlon.event_type_muskathlon').id),
                ('stage_id', '=', self.env.ref(
                    'muskathlon.stage_fill_profile').id)
            ])
            registrations.with_delay().muskathlon_medical_survey_done()
        return res
