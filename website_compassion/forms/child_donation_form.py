##############################################################################
#
#    Copyright (C) 2018-2021 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#    @author: Robin Berguerand <robin.berguerand@gmail.ch>
#    The licence is in the file __manifest__.py
#
##############################################################################
import re

from datetime import datetime

from odoo import models, fields, _


def _get_contract(partner, child):
    """
    Map the contracts accordingly to the given values
    :param partner: the partner to map contracts from
    :param child: the child related to the contract
    :return:
    """
    return (partner.contracts_fully_managed +
            partner.contracts_correspondant +
            partner.contracts_paid).filtered(lambda a: int(a.child_id) == int(child.id))


class ChildDonationForm(models.AbstractModel):
    _name = "cms.form.partner.child.donation"
    _inherit = ["cms.form.payment"]
    _display_type = "full"
    _form_model = "account.invoice"
    gift_type = fields.Many2one("product.product", "Gift type", required=True,
                                domain=[("categ_id.name", "=", "Sponsor gifts")])
    partner = fields.Many2one("res.partner","Partner")
    child_sponsor = fields.Many2one("compassion.child", "Child")
    amount = fields.Float(required=True)

    @property
    def _form_fieldsets(self):
        return [{"id": "Gift", "fields": ["amount", "gift_type"]}]

    def form_init(self, request, main_object=None, **kw):
        form = super().form_init(
            request, main_object, **kw
        )
        # Set default value
        form.child_sponsor = kw["child"]
        form.partner = kw["partner"]
        return form

    def form_title(self):
        if self.child_sponsor.preferred_name:
            return _('Make a gift to %s') % self.child_sponsor.preferred_name
        else:
            return _('Make a gift to %s')

    def _form_create(self, values):
        # Create as superuser
        self.main_object = self.form_model.sudo().create(values.copy())

    @property
    def _payment_success_redirect(self):
        return f"/my/children/donate/payments/validate/{self.invoice_id.id}?payment=success"

    @property
    def _payment_error_redirect(self):
        return f"/my/children/donate/payments/validate/{self.invoice_id.id}?payment=error"

    def generate_invoice(self):
        partner = self.partner
        product = self.gift_type
        name = product.product_tmpl_id.name
        contract_id = _get_contract(partner, self.child_sponsor)
        invoicing = (
            self.env["account.invoice"]
                .sudo()
                .create(
                {
                    "invoice_line_ids": [
                        (
                            0,
                            0,
                            {
                                "quantity": 1,
                                "price_unit": self.amount,
                                "account_id": product.property_account_income_id.id,
                                "name": name,
                                "product_id": product.id,
                                "contract_id": contract_id.id,
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
        return invoicing

    def form_after_create_or_update(self, values, extra_values):
        # Get the extra values of the form
        self.amount = extra_values.get("amount")
        self.gift_type = extra_values.get("gift_type")

        # Skip invoice validation in super to avoid having the analytic of product
        super().form_after_create_or_update(values, extra_values)
