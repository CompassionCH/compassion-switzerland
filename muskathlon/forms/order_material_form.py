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

    class OrderMaterialForm(models.AbstractModel):
        _name = 'cms.form.order.material.mixin'
        _inherit = 'cms.form'

        _form_model = 'crm.lead'
        _form_model_fields = [
            'partner_id', 'description'
        ]
        _form_required_fields = ['flyer_number']

        partner_id = fields.Many2one('res.partner')
        event_id = fields.Many2one('crm.event.compassion')
        form_id = fields.Char()
        flyer_number = fields.Selection([
            ('5', '5'),
            ('10', '10'),
            ('15', '15'),
            ('20', '20'),
            ('30', '30'),
        ], 'Number of flyers')

        @property
        def form_msg_success_created(self):
            return _(
                'Thank you for your request. You will hear back from us '
                'within the next days.'
            )

        @property
        def form_widgets(self):
            # Hide fields
            res = super(OrderMaterialForm, self).form_widgets
            res.update({
                'form_id': 'muskathlon.form.widget.hidden',
                'partner_id': 'muskathlon.form.widget.hidden',
                'event_id': 'muskathlon.form.widget.hidden',
                'description': 'muskathlon.form.widget.hidden',
            })
            return res

        def form_init(self, request, main_object=None, **kw):
            form = super(OrderMaterialForm, self).form_init(
                request, main_object, **kw)
            # Set default values
            registration = kw.get('registration')
            form.partner_id = registration and registration.partner_id
            form.event_id = registration and registration.event_id
            return form

        def form_before_create_or_update(self, values, extra_values):
            """ Dismiss any pending status message, to avoid multiple
            messages when multiple forms are present on same page.
            """
            self.o_request.website.get_status_message()
            staff_id = self.env['staff.notification.settings']\
                .sudo().get_param('muskathlon_lead_notify_id')
            values.update({
                'name': "Muskathlon material order",
                'description': "Number of flyers wanted: " + extra_values[
                    'flyer_number'],
                'user_id': staff_id,
                'event_id': self.event_id.id,
                'partner_id': self.partner_id.id,
            })

        def _form_create(self, values):
            """ Run as Muskathlon user to authorize lead creation. """
            uid = self.env.ref('muskathlon.user_muskathlon_portal').id
            super(OrderMaterialForm, self.sudo(uid))._form_create(values)


    class OrderMaterialFormFlyer(models.AbstractModel):
        _name = 'cms.form.order.material'
        _inherit = 'cms.form.order.material.mixin'

        form_id = fields.Char(default='order_material')


    class OrderMaterialFormChildpack(models.AbstractModel):
        _name = 'cms.form.order.muskathlon.childpack'
        _inherit = 'cms.form.order.material.mixin'

        form_id = fields.Char(default='muskathlon_childpack')
        flyer_number = fields.Selection(string='Number of childpacks')

        def form_before_create_or_update(self, values, extra_values):
            super(OrderMaterialFormChildpack,
                  self).form_before_create_or_update(values, extra_values)
            values.update({
                'name': "Muskathlon childpack order",
                'description': "Number of childpacks wanted: " + extra_values[
                    'flyer_number'],
            })
