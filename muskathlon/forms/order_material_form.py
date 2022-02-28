##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from base64 import b64decode, b64encode

from werkzeug.datastructures import FileStorage

from odoo import models, fields, _

_logger = logging.getLogger(__name__)

try:
    import magic
except ImportError:
    _logger.warning("Please install magic in order to use Muskathlon module")


class OrderMaterialForm(models.AbstractModel):
    _name = "cms.form.order.material.mixin"
    _inherit = "cms.form"

    _form_model = "crm.lead"
    _form_model_fields = ["partner_id", "description"]
    _form_required_fields = ["flyer_german", "flyer_french"]

    partner_id = fields.Many2one("res.partner", readonly=False)
    event_id = fields.Many2one("crm.event.compassion", readonly=False)
    form_id = fields.Char()

    flyers_select = [(i, str(i)) for i in (0, 5, 10, 15, 20, 30)]
    flyer_german = fields.Selection(flyers_select, string="Number of flyers in german", default=0)
    flyer_french = fields.Selection(flyers_select, string="Number of flyers in french", default=0)

    @property
    def _form_fieldsets(self):
        return [
            {"id": "flyers", "fields": ["flyer_german", "flyer_french", "form_id"]},
        ]

    @property
    def form_msg_success_created(self):
        return _(
            "Thank you for your request. You will hear back from us "
            "within the next days."
        )

    @property
    def form_widgets(self):
        # Hide fields
        res = super(OrderMaterialForm, self).form_widgets
        res.update(
            {
                "form_id": "cms_form_compassion.form.widget.hidden",
                "partner_id": "cms_form_compassion.form.widget.hidden",
                "event_id": "cms_form_compassion.form.widget.hidden",
                "description": "cms_form_compassion.form.widget.hidden",
            }
        )
        return res

    @staticmethod
    def create_description(material, values, languages=["french", "german"]):
        lines = []
        for lang in languages:
            if int(values[f'flyer_{lang}']) > 0:
                lines.append(f"<li>{values[f'flyer_{lang}']} <b>{material}</b> in {lang}</li>")
        description = f"<ul>{''.join(lines)}</ul>"
        return description

    def form_init(self, request, main_object=None, **kw):
        form = super(OrderMaterialForm, self).form_init(request, main_object, **kw)
        # Set default values
        registration = kw.get("registration")
        form.partner_id = registration and registration.partner_id
        form.event_id = registration and registration.compassion_event_id
        return form

    def form_before_create_or_update(self, values, extra_values):
        """ Dismiss any pending status message, to avoid multiple
        messages when multiple forms are present on same page.
        """
        super(OrderMaterialForm, self).form_before_create_or_update(
            values, extra_values
        )
        self.o_request.website.get_status_message()
        staff_id = (
            self.env["res.config.settings"]
                .sudo()
                .get_param("muskathlon_order_notify_id")
        )
        values.update(
            {
                "name": f"Muskathlon flyer order - {self.partner_id.name}",
                "description": self.create_description("flyer", extra_values),
                "user_id": staff_id,
                "event_ids": [(4, self.event_id.id, None)],
                "partner_id": self.partner_id.id,
            }
        )

    def form_check_empty_value(self, fname, field, value, **req_values):
        """Invalidate the form if they order 0 flyers"""
        is_valid = super().form_check_empty_value(fname, field, value, **req_values)
        is_valid |= int(req_values["flyer_french"]) + int(req_values["flyer_german"]) <= 0
        return is_valid

    def _form_create(self, values):
        """ Run as Muskathlon user to authorize lead creation. """
        uid = self.env.ref("muskathlon.user_muskathlon_portal").id
        self.main_object = self.form_model.sudo(uid).create(values.copy())

    def form_after_create_or_update(self, values, extra_values):
        super(OrderMaterialForm, self).form_after_create_or_update(
            values, extra_values
        )
        # Update contact fields on lead
        self.main_object._onchange_partner_id()

        # Send mail
        email_template = self.env.ref("muskathlon.order_material_mail_template")
        email_template.sudo().send_mail(
            self.main_object.id,
            raise_exception=False,
            force_send=True,
            email_values={
                "attachments": [("picture.jpg", self.main_object.partner_id.image)],
                "email_to": self.main_object.user_email,
            },
        )
        return True


class OrderMaterialFormFlyer(models.AbstractModel):
    _name = "cms.form.order.material"
    _inherit = "cms.form.order.material.mixin"

    form_id = fields.Char(default="order_material")


class OrderMaterialFormChildpack(models.AbstractModel):
    _name = "cms.form.order.muskathlon.childpack"
    _inherit = "cms.form.order.material.mixin"

    form_id = fields.Char(default="muskathlon_childpack")
    flyer_german = fields.Selection(string="Number of childpacks in german", default=0)
    flyer_french = fields.Selection(string="Number of childpacks in french", default=0)

    def form_before_create_or_update(self, values, extra_values):
        super(OrderMaterialFormChildpack, self).form_before_create_or_update(
            values, extra_values
        )
        values.update(
            {
                "name": f"Muskathlon childpack order - {self.partner_id.name}",
                "description": self.create_description("childpack", extra_values),
            }
        )
