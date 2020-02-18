##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, tools


testing = tools.config.get('test_enable')

# prevent these forms to be registered when running tests
if not testing:

    class UserRegistrationForm(models.AbstractModel):
        """
        A form allowing to register an user account and link it to an existing
        partner
        """
        _inherit = 'cms.form.res.users'

        def _form_create(self, values):
            """ Put in context for sending a communication to the user. """
            super(UserRegistrationForm,
                  self.with_context(create_communication=True)
                  )._form_create(values)

        def _reactivate_users(self, res_users):
            """
            Just send the confirmation in case the users already existed.
            :param res_users: users recordset
            :return: None
            """
            config_id = self.sudo().env.ref(
                'mobile_app_switzerland.mobile_app_welcome_config').id
            self.env['partner.communication.job'].sudo().create({
                'config_id': config_id,
                'object_ids': res_users.ids,
                'partner_id': res_users[:1].partner_id.id,
            })

        def _get_portal_user_vals(self, wizard_id, form_values):
            """ Set the communication to send to user. """
            vals = super()._get_portal_user_vals(
                wizard_id, form_values)
            config_id = self.sudo().env.ref(
                'mobile_app_switzerland.mobile_app_welcome_config').id
            vals['invitation_config_id'] = config_id
            return vals
