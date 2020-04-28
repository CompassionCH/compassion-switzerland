from odoo import models, fields


class CrowdfundingDonationForm(models.AbstractModel):
    _name = "cms.form.crowdfunding.donation"
    _inherit = ["cms.form.payment", "cms.form.match.partner"]

    # form_buttons_template = "cms_form_compassion.modal_form_buttons"
    # form_id = "crowdfunding_donation"

    _form_model = "crowdfunding.participant"
    # Just load the participant partner to avoid security issues with relation fields
    _form_model_fields = ['partner_id']

    # TODO: Use this later once amount is set correctly via javascript
    # Otherwise blocks form and error message on amount isn't visible

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
                ],
            }
        ]

    def _load_partner_field(self, fname, **req_values):
        """ Prevents taking participant partner to fill donor fields. """
        return req_values.get(fname, "")

    # TODO: Adapt payment routes
    @property
    def _payment_success_redirect(self):
        return f"/event/payment/validate/{self.invoice_id.id}?payment=success"

    @property
    def _payment_error_redirect(self):
        return f"/event/payment/validate/{self.invoice_id.id}?payment=error"

    def generate_invoice(self):
        participant = self.main_object.sudo()
        project = participant.project_id
        event = project.event_id
        product = project.product_id
        name = f"[{project.name}] Donation for {participant.partner_id.name}"

        return self.env["account.invoice"].create(
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
                        },
                    )
                ],
                "type": "out_invoice",
                "date_invoice": fields.Date.today(),
                "payment_term_id": self.env.ref(
                    "account.account_payment_term_immediate"
                ).id,
                "partner_id": self.partner_id.id,
            }
        )

    def _form_write(self, values):
        # Don't need to write into crowdfunding.participant object
        pass
