##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields, _


class GroupVisitPaymentForm(models.AbstractModel):
    _name = "cms.form.event.group.visit.payment"
    _inherit = "cms.form.payment"

    event_id = fields.Many2one("crm.event.compassion", readonly=False)
    registration_id = fields.Many2one("event.registration", readonly=False)
    partner_name = fields.Char("Participant", readonly=True)

    @property
    def _payment_redirect(self):
        return f"/event/payment/gpv_payment_validate/{self.invoice_id.id}"

    @property
    def _form_fieldsets(self):
        return [
            {
                "id": "payment",
                "fields": ["partner_name"],
            },
        ]

    @property
    def form_title(self):
        if self.event_id:
            return self.event_id.name + " " + _("payment")
        else:
            return _("Travel payment")

    @property
    def submit_text(self):
        return _("Proceed with payment")

    @property
    def form_widgets(self):
        # Hide fields
        res = super().form_widgets
        res["partner_name"] = "cms_form_compassion.form.widget.readonly"
        return res

    def form_init(self, request, main_object=None, **kw):
        form = super().form_init(request, main_object, **kw)
        # Store ambassador and event in model to use it in properties
        registration = kw.get("registration")
        if registration:
            form.event_id = registration.compassion_event_id
            form.partner_id = registration.partner_id
            form.registration_id = registration
        return form

    def _form_load_partner_name(self, fname, field, value, **req_values):
        return self.partner_id.sudo().name

    def generate_invoice(self):
        # modifiy and add line
        group_visit_invoice = self.registration_id.sudo().group_visit_invoice_id
        # Admin
        analytic_account = (
            self.env["account.analytic.account"]
                .sudo()
                .search([("code", "=", "ATT_ADM")])
        )
        # Financial Expenses
        account = self.env["account.account"].sudo().search([("code", "=", "4200")])
        existing_tax = group_visit_invoice.invoice_line_ids.filtered(
            lambda l: l.account_id == account
        )

        if not existing_tax:
            group_visit_invoice.with_delay().modify_open_invoice(
                {
                    "invoice_line_ids": [
                        (
                            0,
                            0,
                            {
                                "quantity": 1.0,
                                "price_unit": group_visit_invoice.amount_total
                                * 0.019,
                                "account_id": account.id,
                                "name": "Credit card tax",
                                "account_analytic_id": analytic_account.id,
                            },
                        )
                    ]
                }
            )
        return group_visit_invoice

    def _form_create(self, values):
        # Do nothing here
        return True
