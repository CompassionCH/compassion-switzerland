# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import re

from dateutil.relativedelta import relativedelta

from odoo import models, fields, tools, _

testing = tools.config.get('test_enable')


if not testing:
    # prevent these forms to be registered when running tests
    class Step2Forms(models.AbstractModel):
        _name = 'cms.form.group.visit.step2'
        _inherit = 'cms.form'

        _form_model = 'event.registration'
        _form_model_fields = ['completed_task_ids']

        # This allows to recognize that a form was submitted
        form_id = fields.Char()

        @property
        def form_widgets(self):
            # Hide fields
            res = super(Step2Forms, self).form_widgets
            res['form_id'] = 'cms_form_compassion.form.widget.hidden'
            return res

        def form_cancel_url(self, main_object=None):
            """URL to redirect to after click on "cancel" button."""
            main_object = main_object or self.main_object
            if main_object:
                return "/event/{}/agreements".format(main_object.uuid)
            return "/events"

        def _form_write(self, values):
            """Write as superuser to avoid any security restrictions."""
            # pass a copy to avoid pollution of initial values by odoo
            self.main_object.sudo().write(values.copy())

        def _form_validate_alpha_field(self, field, value):
            if value and not re.match(r"^[\w\s'-/]+$", value, re.UNICODE):
                return field, _('Please avoid any special characters')
            # No error
            return 0, 0

    class TravelContractForm(models.AbstractModel):
        _name = 'cms.form.group.visit.travel.contract'
        _inherit = 'cms.form.group.visit.step2'

        _form_required_fields = ['contract_agreement']

        contract_agreement = fields.Boolean('Check to sign the agreements')
        form_id = fields.Char(default='contract')

        @property
        def form_msg_success_updated(self):
            return _('Thank you for having read and signed the travel '
                     'agreements.')

        @property
        def _form_fieldsets(self):
            return [
                {
                    'id': 'agreements',
                    'description': _(
                        "I acknowledge that I have read and accepted the "
                        "conditions mentioned above concerning my meeting "
                        "with the child I am sponsoring. If I do not comply "
                        "with these conditions, Compassion reserves the right "
                        "to cancel my sponsorship."
                    ),
                    'fields': ['contract_agreement', 'form_id']
                },
            ]

        def form_before_create_or_update(self, values, extra_values):
            if extra_values.get('contract_agreement'):
                # Mark the task sign agreement as completed
                sign_task = self.env.ref(
                    'website_event_compassion.task_sign_travel')
                values['completed_task_ids'] = [(4, sign_task.id)]

    class ChildProtectionForm(models.AbstractModel):
        _name = 'cms.form.group.visit.child.protection'
        _inherit = 'cms.form.group.visit.step2'

        _form_required_fields = ['final_question']

        final_question = fields.Selection([
            ('yes_free', 'Yes, in an open place and taking into account the '
                         'indications of Compassion.'),
            ('no', 'No, the Compassion Charter does not allow me to be alone '
                   'with a child in any situation. I must always be '
                   'accompanied by someone.'),
            ('yes_my', 'Yes, if he or she is my sponsored child, I can speak '
                       'with him or her alone, regardless of the context.')
        ], 'Your answer')
        form_id = fields.Char(default='child_protection')

        def _form_validate_final_question(self, value, **req_values):
            if value and value != 'no':
                return 'final_question', _(
                    'Please review carefully the Compassion Child Protection '
                    'Charter and answer this question again.')
            # No error
            return 0, 0

        @property
        def form_msg_success_updated(self):
            return _('Thank you for reading the child protection charter '
                     'carefully.')

        @property
        def _form_fieldsets(self):
            return [
                {
                    'id': 'question',
                    'title': _(
                        "Please answer the following question before "
                        "confirming acceptance of the charter:"
                    ),
                    'description': _(
                        'Am I allowed to chat alone with a child during a '
                        'visit to Compassion activities (please select the '
                        'appropriate answer)?'
                    ),
                    'fields': ['form_id']
                },
                {
                    'id': 'final_answer',
                    'description': _(
                        "With my answer, I acknowledge that I have read and "
                        "fully understand the content of the Child Protection "
                        "Charter. I agree with all the conditions mentioned "
                        "above. If I do not comply with these conditions,"
                        "Compassion reserves the right to cancel my "
                        "sponsorship."
                    ),
                    'fields': ['final_question']
                }
            ]

        def form_before_create_or_update(self, values, extra_values):
            if extra_values.get('final_question') == 'no':
                # Mark the task child protection agreement as completed
                sign_task = self.env.ref(
                    'website_event_compassion.task_sign_child_protection')
                values['completed_task_ids'] = [(4, sign_task.id)]

        def form_after_create_or_update(self, values, extra_values):
            # Mark the charter as accepted in the partner
            self.main_object.sudo().partner_id\
                .agree_to_child_protection_charter()

    class TripForm(models.AbstractModel):
        _name = 'cms.form.group.visit.trip.form'
        _inherit = 'cms.form.group.visit.step2'

        _form_model_fields = [
            'birth_name', 'passport_number', 'passport_expiration_date',
            'emergency_name', 'emergency_phone', 'emergency_relation_type',
            'completed_task_ids', 'passport'
        ]
        _form_required_fields = [
            'birth_name', 'passport_number', 'passport_expiration_date',
            'emergency_name', 'emergency_phone', 'emergency_relation_type',
            'passport'
        ]

        form_id = fields.Char(default='travel')
        passport = fields.Binary()

        @property
        def form_widgets(self):
            res = super(TripForm, self).form_widgets
            res['passport'] = 'cms_form_compassion.form.widget.document'
            res['passport_expiration_date'] = 'cms.form.widget.date.ch',
            return res

        @property
        def form_msg_success_updated(self):
            return _('Trip information updated.')

        @property
        def _form_fieldsets(self):
            return [
                {
                    'id': 'passport',
                    'title': _('Passport information'),
                    'fields': [
                        'passport', 'birth_name',
                        'passport_number', 'passport_expiration_date',
                        'form_id'
                    ]
                },
                {
                    'id': 'emergency',
                    'title': _('Person of contact'),
                    'description': _('Please indicate a contact in case of '
                                     'emergency during the trip.'),
                    'fields': [
                        'emergency_relation_type',
                        'emergency_name', 'emergency_phone'
                    ]
                },
            ]

        def _form_validate_emergency_phone(self, value, **req_values):
            if value and not re.match(r'^[+\d][\d\s]{7,}$', value, re.UNICODE):
                return 'emergency_phone', _(
                    'Please enter a valid phone number')
            # No error
            return 0, 0

        def _form_validate_passport(self, value, **req_values):
            if value == '':
                return 'passport', _('Missing')
            return 0, 0

        def _form_validate_passport_number(self, value, **req_values):
            return self._form_validate_alpha_field('passport_number', value)

        def _form_validate_emergency_name(self, value, **req_values):
            return self._form_validate_alpha_field('emergency_name', value)

        def _form_validate_birth_name(self, value, **req_values):
            return self._form_validate_alpha_field('birth_name', value)

        def _form_validate_passport_expiration_date(self, value, **req_values):
            if value:
                valid = True
                old = False
                try:
                    date = fields.Date.from_string(value)
                    limit_date = fields.Date.from_string(
                        self.main_object.compassion_event_id.end_date
                    ) + relativedelta(months=6)
                    old = date < limit_date
                    valid = not old
                except ValueError:
                    valid = False
                finally:
                    if not valid:
                        message = _("Please enter a valid date")
                        if old:
                            message = _(
                                "Your passport must be renewed! It should be "
                                "valid at least six months after your return.")
                        return 'passport_expiration_date', message
            # No error
            return 0, 0

        def form_before_create_or_update(self, values, extra_values):
            # Mark tasks as done
            completed_tasks = []
            if values.get('passport_number') and values.get(
                    'passport_expiration_date'):
                completed_tasks.append((
                    4, self.env.ref(
                        'website_event_compassion.task_passport').id))
            if values.get('emergency_name'):
                completed_tasks.append((
                    4, self.env.ref(
                        'website_event_compassion.task_urgency_contact').id))
            values['completed_task_ids'] = completed_tasks

    class CriminalForm(models.AbstractModel):
        _name = 'cms.form.group.visit.criminal.record'
        _inherit = 'cms.form.group.visit.step2'

        _form_model_fields = ['criminal_record']
        _form_required_fields = ['criminal_record']

        form_id = fields.Char(default='criminal')
        criminal_record = fields.Binary()

        @property
        def _form_fieldsets(self):
            return [
                {
                    'id': 'criminal',
                    'fields': ['criminal_record', 'form_id']
                },
            ]

        @property
        def form_msg_success_updated(self):
            return _('Criminal record successfully uploaded.')

        @property
        def form_widgets(self):
            # Hide fields
            res = super(CriminalForm, self).form_widgets
            res['criminal_record'] = 'cms_form_compassion.form.widget.document'
            return res

        def _form_validate_criminal_record(self, value, **req_values):
            if value == '':
                return 'criminal_record', _('Missing')
            return 0, 0

        def form_before_create_or_update(self, values, extra_values):
            if values.get('criminal_record'):
                # Mark the task criminal record as completed
                criminal_task = self.env.ref(
                    'website_event_compassion.task_criminal')
                values['completed_task_ids'] = [(4, criminal_task.id)]
            else:
                del values['completed_task_ids']
