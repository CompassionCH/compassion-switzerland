# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from odoo import models, fields, tools, _

testing = tools.config.get('test_enable')
_logger = logging.getLogger(__name__)

try:
    import magic
except ImportError:
    _logger.warning('Please install magic in order to use Muskathlon module')


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
                'form_id': 'cms_form_compassion.form.widget.hidden',
                'partner_id': 'cms_form_compassion.form.widget.hidden',
                'event_id': 'cms_form_compassion.form.widget.hidden',
                'description': 'cms_form_compassion.form.widget.hidden',
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
            super(OrderMaterialForm, self).form_before_create_or_update(
                values, extra_values)
            self.o_request.website.get_status_message()
            staff_id = self.env['staff.notification.settings']\
                .sudo().get_param('muskathlon_order_notify_id')
            values.update({
                'name': "Muskathlon material order - {}".format(
                    self.partner_id.name),
                'description': "Number of flyers wanted: " + extra_values[
                    'flyer_number'],
                'user_id': staff_id,
                'event_id': self.event_id.id,
                'partner_id': self.partner_id.id,
            })

        def _form_create(self, values):
            """ Run as Muskathlon user to authorize lead creation. """
            uid = self.env.ref('muskathlon.user_muskathlon_portal').id
            self.main_object = self.form_model.sudo(uid).create(values.copy())

        def form_after_create_or_update(self, values, extra_values):
            super(OrderMaterialForm, self).form_after_create_or_update(
                values, extra_values)
            # Update contact fields on lead
            self.main_object._onchange_partner_id()

    class OrderMaterialFormFlyer(models.AbstractModel):
        _name = 'cms.form.order.material'
        _inherit = 'cms.form.order.material.mixin'

        form_id = fields.Char(default='order_material')

        def form_after_create_or_update(self, values, extra_values):
            super(OrderMaterialFormFlyer, self).form_after_create_or_update(
                values, extra_values)
            # Attach ambassador picture for flyer creation
            ftype = 'jpg'
            partner = self.main_object.partner_id
            mimetype = magic.from_buffer(partner.image.decode('base64'), True)
            if mimetype and '/' in mimetype:
                ftype = mimetype.split('/')[-1]
            filename = '{}.{}'.format(partner.name, ftype)
            uid = self.env.ref('muskathlon.user_muskathlon_portal').id
            self.env['ir.attachment'].sudo(uid).create({
                'res_model': 'crm.lead',
                'res_id': self.main_object.id,
                'datas': partner.image,
                'datas_fname': filename,
                'name': filename
            })

    class OrderMaterialFormChildpack(models.AbstractModel):
        _name = 'cms.form.order.muskathlon.childpack'
        _inherit = 'cms.form.order.material.mixin'

        form_id = fields.Char(default='muskathlon_childpack')
        flyer_number = fields.Selection(string='Number of childpacks')

        def form_before_create_or_update(self, values, extra_values):
            super(OrderMaterialFormChildpack,
                  self).form_before_create_or_update(values, extra_values)
            values.update({
                'name': "Muskathlon childpack order - {}".format(
                    self.partner_id.name),
                'description': "Number of childpacks wanted: " + extra_values[
                    'flyer_number'],
            })
