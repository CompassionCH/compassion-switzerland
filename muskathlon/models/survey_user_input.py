# -*- coding: utf-8 -*-
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
    _inherit = 'survey.user_input'

    @api.multi
    def write(self, vals):
        """
        Automatically complete Medical Survey task when user filled it
        """
        res = super(SurveyUserInput, self).write(vals)
        if vals.get('state') == 'done':

            # Search for medical surveys
            for registration in self.env['event.registration'].search([
                ('medical_survey_id', 'in', self.ids),
                ('partner_id_id', '=', self.partner_id.id)
            ]):
                # if conditions to check that the task is the correct one,
                # same as survey in event definition
                registration.write({
                    'completed_task_ids': [
                        (4, self.env.ref(
                            'website_event_compassion.task_medical_survey').id)
                    ]
                })

        return res
