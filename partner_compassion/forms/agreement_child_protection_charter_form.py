# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Christopher Meier <dev@c-meier.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields, tools, _

testing = tools.config.get('test_enable')


if not testing:
    # prevent these forms to be registered when running tests

    class ChildProtectionForm(models.AbstractModel):
        _name = 'cms.form.partner.child.protection.charter'
        _inherit = 'cms.form'

        _form_model = 'res.partner'
        _form_required_fields = ['charter_agreement']

        charter_agreement = fields.Boolean('Check to agree to this charter')

        @property
        def form_msg_success_updated(self):
            return _('Thank you for reading the child protection charter '
                     'carefully.')

        @property
        def _form_fieldsets(self):
            return [
                {
                    'id': 'agreements',
                    'description': _(
                        "I acknowledge that I have read and "
                        "fully understood the content of the Child Protection "
                        "Charter. I agree with all the conditions mentioned "
                        "above. If I do not comply with these conditions,"
                        "Compassion reserves the right to deactivate my "
                        "translator account and cancel my sponsorships."
                    ),
                    'fields': ['charter_agreement']
                }
            ]

        def form_cancel_url(self, main_object=None):
            """URL to redirect to after click on "cancel" button."""
            main_object = main_object or self.main_object
            if main_object:
                return "/partner/{}/child-protection-charter"\
                    .format(main_object.uuid)
            return "/"

        def _form_write(self, values):
            # This overload is used to prevent the form from writing all the
            # fields. Because the default behaviour when the _form_model_fields
            # variable is an empty list (which it is by default) is to use all
            # the fields present in the model.
            # Another solution would be to add a non-existent field name to the
            # _form_model_fields variable.
            # Ex. _form_model_fields = ['does_not_exists']
            pass

        def form_before_create_or_update(self, write_values, extra_values):
            pass

        def form_after_create_or_update(self, values, extra_values):
            if extra_values.get('charter_agreement'):
                self.main_object.sudo().agree_to_child_protection_charter()
