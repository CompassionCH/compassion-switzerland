##############################################################################
#
#    Copyright (C) 2018-2020 Compassion CH (http://www.compassion.ch)
#    @author: Théo Nikles <theo.nikles@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, _
from math import ceil


class PaymentOptionsForm(models.AbstractModel):
    _name = "cms.form.payment.options"
    _inherit = "cms.form"

    form_buttons_template = "cms_form_compassion.modal_form_buttons"
    form_id = "modal_payment_options"
    _form_model = "recurring.contract.group"

    payment_mode = fields.Selection(selection=[
        # CO-3574 TODO activate LSV/DD with bank authorization form
        # ("LSV", "LSV"),
        # ("Postfinance Direct Debit", "Postfinance Direct Debit"),
        ("Permanent Order", "Permanent Order"),
    ], help="Don't forget to change your standing order accordingly. "
            "Please contact us if you want to setup a Direct Debit or LSV "
            "automatic withdrawal.")
    payment_frequency = fields.Selection(selection=[
        ("1 month", "1 month"),
        ("2 month", "2 months"),
        ("3 month", "3 months"),
        ("4 month", "4 months"),
        ("6 month", "6 months"),
        ("1 year", "1 year"),
    ])
    bvr_reference = None

    _form_model_fields = [
        "advance_billing_months",
        "recurring_unit",
        "bvr_reference",
        "payment_mode_id"
    ]
    _form_fields_order = [
        # "payment_mode", TODO remove comment when payment mode change is ready
        "payment_frequency",
    ]

    def _form_load_payment_mode(self, fname, field, value, **req_values):
        payment = self.main_object.with_context(lang="en_US")\
            .payment_mode_id.name
        return next((payment for modes in self._fields["payment_mode"]
                    .selection if payment in modes), None)

    def _form_load_payment_frequency(self, fname, field, value, **req_values):
        group = self.main_object
        return f"{group.advance_billing_months} {group.recurring_unit}"

    @property
    def form_title(self):
        return _("Payment options")

    @property
    def submit_text(self):
        return _("Save")

    @property
    def form_msg_success_updated(self):
        return _("Payment options updated.")

    def form_init(self, request, main_object=None, **kw):
        form = super(PaymentOptionsForm, self).form_init(
            request, main_object.sudo(), **kw
        )
        # Set default value
        form.bvr_reference = kw["bvr_reference"]
        return form

    def _if_needed(self, dic):
        """
        Update the dictionary only if needed. If values changes from stored
        :param dic: the dic to check
        :return: dic with non needed key removed
        """
        res = {}
        for key, val in dic.items():
            if not self.main_object[key] == val:
                res.update({key: val})

        # manual check for payment_mode_id
        if "payment_mode_id" in dic and dic["payment_mode_id"] == self.main_object["payment_mode_id"].id:
            del res["payment_mode_id"]

        return res

    def form_extract_values(self, **request_values):
        values = super(PaymentOptionsForm, self).form_extract_values(
            **request_values
        )

        group_vals = {}

        key = "payment_mode"
        if key in values:
            if values[key]:
                payment_mode_id = self.env["account.payment.mode"]\
                    .with_context(lang="en_US").search([
                        ("name", "=", values[key]),
                    ])
                group_vals.update({
                    "payment_mode_id": payment_mode_id.id,
                })

                # Handle BVR reference for Permanent Order
                if values[key] == "Permanent Order":
                    if not self.bvr_reference:
                        raise ValueError(
                            "Permanent Order needs a BVR reference."
                        )
                    group_vals.update({
                        "bvr_reference": self.bvr_reference,
                    })
            del values[key]

        key = "payment_frequency"
        if key in values:
            if values[key]:
                value, unit = values[key].split()
                group_vals.update({
                    "advance_billing_months": value,
                    "recurring_unit": unit,
                })
            del values[key]

        return self._if_needed(group_vals)


class PaymentOptionsMultipleForm(models.AbstractModel):
    _name = "cms.form.payment.options.multiple"
    _inherit = "cms.form.payment.options"

    form_id = "modal_payment_options_multiple"

    _form_required_fields = [
        "payment_mode",
        "payment_frequency",
    ]

    @property
    def form_title(self):
        return _("Merge payment groups")

    @property
    def form_msg_success_updated(self):
        return _("Payment groups merged.")

    @property
    def _form_fieldsets(self):
        return [
            {
                "id": "modal_payment_options_multiple",
                "description": _(
                    "Note that merging is an operation that cannot be undone. "
                    "Your different groups will be fused together with one "
                    "payment method, payment frequency."
                ),
                "fields": [
                    "payment_mode",
                    "payment_frequency",
                ]
            }
        ]

    def form_extract_values(self, **request_values):
        def filter_fun(c):
            return c.state not in ["cancelled", "terminated"] and \
                   partner == c.mapped("partner_id")

        selected_group = self.main_object
        partner = selected_group.partner_id
        # Select only groups with a sponsorship not cancelled nor terminated
        groups = (
                partner.contracts_fully_managed.filtered(filter_fun) +
                partner.contracts_correspondant.filtered(filter_fun) +
                partner.contracts_paid.filtered(filter_fun)
        ).mapped("group_id")
        # Select ALL the contracts in the groups; some groups will be unlinked
        contracts = groups.mapped("contract_ids")
        for contract in contracts:
            contract.write({"group_id": selected_group.id})
        for group in groups:
            if group != selected_group:
                group.unlink()

        return super(PaymentOptionsMultipleForm, self).form_extract_values(
            **request_values
        )
