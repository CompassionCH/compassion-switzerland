from odoo import models, fields


class CrowdfundingDonationForm(models.AbstractModel):
    _name = "cms.form.crowdfunding.donation"
    _inherit = ["cms.form.payment", "cms.form.match.partner"]

    # form_buttons_template = "cms_form_compassion.modal_form_buttons"
    # form_id = "crowdfunding_donation"

    _form_model = "account.invoice"
    _form_model_fields = [
        "partner_title",
        "partner_firstname",
        "partner_lastname",
        "partner_email",
        "partner_phone",
        "partner_street",
        "partner_zip",
        "partner_city",
        "partner_country_id",
    ]

    # TODO: Use this later once amount is set correctly via javascript
    # Otherwise blocks form and error message on amount isn't visible

    # @property
    # def _form_fieldsets(self):
    #     return [
    #         {
    #             "id": "partner",
    #             "fields": [
    #                 "partner_title",
    #                 "partner_firstname",
    #                 "partner_lastname",
    #                 "partner_email",
    #                 "partner_phone",
    #                 "partner_street",
    #                 "partner_zip",
    #                 "partner_city",
    #                 "partner_country_id",
    #             ],
    #         }
    #     ]

    # TODO: Adapt payment routes
    @property
    def _payment_success_redirect(self):
        return f"/event/payment/validate/{self.invoice_id.id}?payment=success"

    @property
    def _payment_error_redirect(self):
        return f"/event/payment/validate/{self.invoice_id.id}?payment=error"

    # def form_init(self, request, main_object=None, **kw):
    #     form = super().form_init(request, main_object, **kw)

    #     # Does not work
    #     form.project = kw.get("project")

    #     return form

    # Didn't get there yet
    # def generate_invoice(self):
    #     project = self.project
    #     product = project.product_id
    #     # ambassador = self.ambassador_id.sudo()
    #     name = f"[{project.name}] Donation for"

    #     return self.env["account.invoice"].create(
    #         {
    #             "name": name,
    #             "origin": name,
    #             "invoice_line_ids": [
    #                 (
    #                     0,
    #                     0,
    #                     {
    #                         "quantity": 1.0,
    #                         "price_unit": self.amount,
    #                         "account_id": product.property_account_income_id.id,
    #                         "name": name,
    #                         "product_id": product.id,
    #                         "account_analytic_id": event.analytic_id.id,
    #                         "user_id": ambassador.id,
    #                     },
    #                 )
    #             ],
    #             "type": "out_invoice",
    #             "date_invoice": fields.Date.today(),
    #             "payment_term_id": self.env.ref(
    #                 "account.account_payment_term_immediate"
    #             ).id,
    #             "partner_id": self.partner_id.id,
    #         }
    #     )

    # # Doesn't seem to do anything
    # def _form_create(self, values):
    #     # Create as superuser
    #     self.main_object = self.form_model.sudo().create(values.copy())
