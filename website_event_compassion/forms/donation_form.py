##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields, _


class EventDonationForm(models.AbstractModel):
    _name = "cms.form.event.donation"
    _inherit = ["cms.form.payment", "cms.form.match.partner"]

    # The form is inside a participant details page
    form_buttons_template = "cms_form_compassion.modal_form_buttons"
    form_id = "modal_donation"
    _form_model = "account.invoice"

    amount = fields.Float("Amount (CHF)", required=True)
    ambassador_id = fields.Many2one("res.partner", readonly=False)
    event_id = fields.Many2one("crm.event.compassion", readonly=False)
    gtc_accept = fields.Boolean("Terms and conditions", required=True)
    partner_opt_out = fields.Boolean("Unsubscribe from e-mails")

    # Make address fields mandatory
    partner_street = fields.Char(required=True)
    partner_zip = fields.Char(required=True)
    partner_city = fields.Char(required=True)

    def _form_validate_amount(self, value, **kwargs):
        try:
            if not value or float(value) < 1:
                return "amount", _("Please set an amount")
        except ValueError:
            return "amount", _("Please set a valid amount (only numbers)")
        return 0, 0

    @property
    def _payment_redirect(self):
        return f"/event/payment/validate/{self.invoice_id.id}"

    @property
    def _form_fieldsets(self):
        return [
            {"id": "payment", "fields": ["amount"]},
            {
                "id": "partner",
                "title": _("Your coordinates"),
                "description": "",
                "fields": [
                    "partner_title",
                    "partner_firstname",
                    "partner_lastname",
                    "partner_email",
                    "partner_phone",
                    "partner_street",
                    "partner_zip",
                    "partner_city",
                    "partner_country_id",
                    "partner_birthdate_date",
                ],
            },
            {
                "id": "gtc",
                "title": _("Data protection"),
                "description": _(
                    "By submitting, you consent that we collect "
                    "your personal information according to our data "
                    "policy. You can unsubscribe from our e-mailing lists "
                    "if you don't want to receive information from "
                    "Compassion."
                ),
                "fields": ["partner_opt_out", "gtc_accept"],
            },
        ]

    @property
    def form_widgets(self):
        # Hide fields
        res = super().form_widgets
        res.update(
            {
                "gtc_accept": "cms_form_compassion.form.widget.terms",
                "partner_birthdate_date": "cms.form.widget.date.ch",
            }
        )
        return res

    @property
    def gtc(self):
        statement = (
            self.env["compassion.privacy.statement"].sudo().search([], limit=1)
        )
        return statement.text

    @property
    def form_title(self):
        if self.ambassador_id:
            return _("Donation for ") + self.ambassador_id.sudo().preferred_name
        else:
            return _("Donation")

    @property
    def submit_text(self):
        return _("Next")

    @property
    def submit_icon(self):
        return "fa-gift"

    def form_init(self, request, main_object=None, **kw):
        form = super().form_init(request, main_object, **kw)
        # Store ambassador and event in model to use it in properties
        registration = kw.get("registration")
        if registration:
            form.event_id = registration.compassion_event_id
            form.ambassador_id = registration.partner_id
        return form

    def generate_invoice(self):
        event = self.event_id.sudo()
        product = event.odoo_event_id.donation_product_id
        ambassador = self.ambassador_id.sudo()
        name = f"[{event.name}] Donation for {ambassador.name}"
        return self.env["account.invoice"].sudo().create(
            {
                "name": name,
                "origin": name,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "quantity": 1.0,
                            "price_unit": self.amount,
                            "account_id": product.property_account_income_id.id,
                            "name": name,
                            "product_id": product.id,
                            "account_analytic_id": event.analytic_id.id,
                            "user_id": ambassador.id,
                        },
                    )
                ],
                "type": "out_invoice",
                "date_invoice": fields.Date.today(),
                "payment_term_id": self.env.ref(
                    "account.account_payment_term_immediate"
                ).id,
                "partner_id": self.partner_id.sudo().id,
            }
        )

    def _form_create(self, values):
        # Create as superuser
        self.main_object = self.form_model.sudo().create(values.copy())

    def form_after_create_or_update(self, values, extra_values):
        """ Mark the privacy statement as accepted.
        """
        self.amount = extra_values.get("amount")
        super().form_after_create_or_update(values, extra_values)
        partner = (
            self.env["res.partner"].sudo().browse(values.get("partner_id")).exists()
        )
        partner.set_privacy_statement(origin="event_donation")
