# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
from odoo import models, api
from odoo.tools import safe_eval


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

            # Search for medical surveys
            registrations = self.env['event.registration'].sudo().search([
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

            # here we need to send a mail to the muskathlon doctor
            icp_obj = self.env['ir.config_parameter']

            muskathlon_doctor_email = safe_eval(
                icp_obj.get_param('muskathlon_doctor_email')
            )

            # send mail only if there is a doctor email address
            if muskathlon_doctor_email:

                # generate pdf from report
                pdf = base64.encodestring(
                    self.env['report'].sudo().get_pdf(self.ids, 'muskathlon.muskathlon_medical_survey'))

                # save pdf as attachment
                ATTACHMENT_NAME = "Muskathlon Medical Survey"
                attachment_data = {
                    'name': ATTACHMENT_NAME,
                    'type': 'binary',
                    'datas': pdf,
                    'datas_fname': ATTACHMENT_NAME + '.pdf',
                    'store_fname': ATTACHMENT_NAME,
                    'res_model': self._name,
                    'res_id': self.id,
                    'mimetype': 'application/x-pdf'
                }

                template = self.env.ref(
                    "muskathlon.muskathlon_medical_survey_to_doctor_template")
                template.with_context(email_to=muskathlon_doctor_email) \
                    .send_mail(self.id, force_send=True, email_values=attachment_data)

        return res
