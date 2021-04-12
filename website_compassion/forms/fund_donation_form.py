##############################################################################
#
#    Copyright (C) 2021 Compassion CH (http://www.compassion.ch)
#    @author: Jonathan Guerne <guernej@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields, _


class FundDonationForm(models.AbstractModel):
    _name = "cms.form.fund.donation"
    _inherit = ["cms.form.payment"]

    _display_type = "full"
    _form_model = "res.partner"

    amount = fields.Float(required=True)
    fund = fields.Many2one("product.product")

    _form_model_fields = [
        "amount",
    ]
    _form_fields_hidden = ("invoice_id", "fund")

    def _form_validate_amount(self, value, **kwargs):
        if not value or not value.isnumeric() or float(value) < 1:
            return "amount", _("Please set an amount")
        return 0, 0

    @property
    def _payment_success_redirect(self):
        return f"/my/new/donation/validate/{self.invoice_id.id}?payment=success"

    @property
    def _payment_error_redirect(self):
        # TODO this property is called when redirecting user for payment but never used later on
        return f"/my/new/donation/validate/{self.invoice_id.id}?payment=error"

    @property
    def form_description(self):
        return self.fund.description

    @property
    def form_title(self):
        if self.fund:
            return _("Donation for ") + self.fund.name
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
        # Store fund to use it in properties
        fund = kw.get("selected_fund")
        if fund:
            form.fund = fund
        return form

    def generate_invoice(self):
        fund = self.fund.sudo()
        name = f"Donation for {fund.name}"
        partner = self.main_object.sudo()
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
                            "account_id": fund.property_account_income_id.id,
                            "name": name,
                            "product_id": fund.id,
                        },
                    )
                ],
                "type": "out_invoice",
                "date_invoice": fields.Date.today(),
                "payment_term_id": self.env.ref(
                    "account.account_payment_term_immediate"
                ).id,
                "partner_id": partner.id,
            }
        )

    def _form_create(self, values):
        # Create as superuser
        self.main_object = self.form_model.sudo().create(values.copy())

    def form_after_create_or_update(self, values, extra_values):
        """ extract amount from form
        """
        self.amount = extra_values.get("amount")
        super().form_after_create_or_update(values, extra_values)
