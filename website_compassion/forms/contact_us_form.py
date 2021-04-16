##############################################################################
#
#    Copyright (C) 2021 Compassion CH (http://www.compassion.ch)
#    @author: Jonathan Guerne <guernej@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields, _
from odoo.tools import html_escape as escape


class TextAreaWidget(models.AbstractModel):
    _name = "website_compassion.form.widget.textarea"
    _inherit = "cms.form.widget.mixin"
    _w_template = "website_compassion.field_widget_textarea"


class ContactUsForm(models.AbstractModel):
    """
    Form to create a new claim
    """

    _name = "cms.form.claim.contact.us"
    _inherit = "cms.form"

    _form_model = "crm.claim"
    _form_model_fields = ["partner_id", "name", "subject", "categ_id"]
    _form_required_fields = ["name", "subject"]

    partner_id = fields.Many2one("res.partner", readonly=False)
    categ_id = fields.Selection(
        lambda x: [(y.id, y.name) for y in x.env["crm.claim.category"].sudo().search([])],
        string="Request Category"
    )

    name = fields.Char("Question / Comment")
    subject = fields.Char("Request subject")

    def form_title(self):
        return _("Contact Us")

    def form_description(self):
        return _("Get in touch by filling the form below")

    @property
    def _form_fieldsets(self):
        fields = [
            {"id": "category",
             "description": _("Select a category from the list that match your request."),
             "fields": ["categ_id"]},
            {"id": "subject",
             "fields": ["subject", "partner_id"]},
            {"id": "question",
             "fields": ["name"]},
        ]

        return fields

    @property
    def form_widgets(self):
        # Hide fields
        res = super(ContactUsForm, self).form_widgets
        res.update(
            {
                "partner_id": "cms_form_compassion.form.widget.hidden",
                "name": "website_compassion.form.widget.textarea",
            }
        )
        return res

    def form_before_create_or_update(self, values, extra_values):
        super().form_before_create_or_update(values, extra_values)
        values.update({
            "partner_id": self.partner_id.id,
            "user_id": False,
            "language": self.main_object.detect_lang(values.get("name")).lang_id.code,
            "email_from": self.partner_id.email,

        })

    def form_after_create_or_update(self, values, extra_values):
        super().form_after_create_or_update(values, extra_values)

        subject = values.get("subject")
        body = values.get("name")
        partner = self.partner_id

        self.main_object.message_post(
            body=body,
            subject=_("Original request from %s %s ") % (partner.firstname, partner.lastname),
        )

        self.env["mail.mail"].sudo().create(
            {
                "state": "sent",
                "subject": subject,
                "body_html": body,
                "author_id": partner.id,
                "email_from": partner.email,
                "mail_message_id": self.env["mail.message"].sudo().create(
                    {
                        "model": "res.partner",
                        "res_id": partner.id,
                        "body": escape(body),
                        "subject": subject,
                        "author_id": partner.id,
                        "subtype_id": self.env.ref("mail.mt_comment").id,
                        "date": fields.Datetime.now(),
                    }
                ).id,
            })

    def _form_create(self, values):
        self.main_object = self.form_model.sudo().create(values.copy())

    def form_init(self, request, main_object=None, **kw):
        form = super().form_init(request, main_object=main_object, **kw)
        form.partner_id = kw.get("partner_id")
        return form
