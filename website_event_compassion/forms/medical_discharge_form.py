# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, tools, _

testing = tools.config.get('test_enable')


if not testing:
    # prevent these forms to be registered when running tests
    class MedicalDischargeForm(models.AbstractModel):
        _name = 'cms.form.group.visit.medical.discharge'
        _inherit = 'cms.form.group.visit.step2'

        _form_model_fields = ['medical_discharge']
        _form_required_fields = ['medical_discharge']

        medical_discharge = fields.Binary()

        @property
        def _form_fieldsets(self):
            return [
                {
                    'id': 'medical_discharge',
                    'fields': ['medical_discharge']
                },
            ]

        @property
        def form_title(self):
            return _("Upload your medical discharge")

        @property
        def form_msg_success_updated(self):
            return _('Medical discharge successfully uploaded.')

        @property
        def form_widgets(self):
            res = super(MedicalDischargeForm, self).form_widgets
            res['medical_discharge'] = 'cms_form_compassion.form.widget' \
                '.document'
            return res

        def _form_validate_medical_discharge(self, value, **req_values):
            if value == '':
                return 'medical_discharge', _('Missing')
            return 0, 0

        def form_before_create_or_update(self, values, extra_values):
            if values.get('medical_discharge'):
                # Mark the task medical discharge task as completed
                criminal_task = self.env.ref(
                    'website_event_compassion.task_medical_discharge')
                values['completed_task_ids'] = [(4, criminal_task.id)]
            else:
                del values['completed_task_ids']
