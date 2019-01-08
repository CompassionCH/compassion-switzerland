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
            registrations = self.env['event.registration'].search([
                ('partner_id', 'in', self.mapped('partner_id').ids),
                ('event_id.event_type_id', '=', self.env.ref(
                    'muskathlon.event_type_muskathlon').id),
                ('stage_id', '=', self.env.ref(
                    'muskathlon.stage_fill_profile').id)
            ])

            # if conditions to check that the task is the correct one,
            # same as survey in event definition
            registrations.write({
                'completed_task_ids': [
                    (4, self.env.ref(
                        'muskathlon.task_medical').id)
                ]
            })
        return res
