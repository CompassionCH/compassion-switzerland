from odoo import models, fields


class CrowdfundingDonationForm(models.AbstractModel):
    _name = "cms.form.crowdfunding.donation"
    _inherit = ["cms.form.payment", "cms.form.match.partner"]

    _form_model = "crowdfunding.participant"

    # Just load the participant partner to avoid security issues with relation fields
    _form_model_fields = ["partner_id"]
    _form_fields_hidden = ("amount",)

    amount = fields.Float(required=True)
    anonymous_donation = fields.Boolean(
        help="""I would like to donate anonymously,
        please do not mention my name in the donors list."""
    )

    @property
    def _form_fieldsets(self):
        return [
            {
                "id": "partner",
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
                    "anonymous_donation",
                ],
            },
        ]

    def _load_partner_field(self, fname, **req_values):
        """ Prevents taking participant partner to fill donor fields. """
        return req_values.get(fname, "")

    @property
    def _payment_success_redirect(self):
        return f"/crowdfunding/payment/validate/{self.invoice_id.id}?payment=success"

    @property
    def _payment_error_redirect(self):
        return f"/crowdfunding/payment/validate/{self.invoice_id.id}?payment=error"

    def generate_invoice(self):
        participant = self.main_object.sudo()
        project = participant.project_id
        event = project.event_id
        product = project.product_id
        name = f"[{project.name}] Donation for {participant.partner_id.name}"
        partner = self.partner_id.sudo()
        partner.write({"state": "active"})

        return (
            self.env["account.invoice"]
            .sudo()
            .create(
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
                                "user_id": participant.id,
                                "crowdfunding_participant_id": participant.id,
                                "crowdfunding_project_id": project.id,
                                "is_anonymous": self.is_anonymous,
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
        )

    def _form_write(self, values):
        # Don't need to write into crowdfunding.participant object
        pass

    def form_after_create_or_update(self, values, extra_values):
        # Get the extra values of the form
        self.amount = extra_values.get("amount")
        self.is_anonymous = extra_values.get("anonymous_donation")
        super().form_after_create_or_update(values, extra_values)
