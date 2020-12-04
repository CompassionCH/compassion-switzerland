##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields
from datetime import date


class AccountInvoice(models.Model):
    """
    Make Invoice translatable for communications with dates.
    """

    _inherit = ["account.invoice", "translatable.model"]
    _name = "account.invoice"

    # Gender field is mandatory for translatable models
    gender = fields.Char(compute="_compute_gender")

    def _compute_gender(self):
        for i in self:
            i.gender = "M"


class Contract(models.Model):
    _inherit = "recurring.contract"

    amount_due = fields.Integer(compute="_compute_amount_due", store=True)

    def _compute_amount_due(self):
        this_month = date.today().replace(day=1)
        for contract in self:
            if (
                    contract.child_id.project_id.suspension != "fund-suspended"
                    and contract.type != "SC"
            ):
                invoice_lines = contract.invoice_line_ids.with_context(
                    lang="en_US"
                ).filtered(
                    lambda i: i.state == "open"
                    and i.due_date < this_month
                    and i.invoice_id.invoice_type == "sponsorship"
                )
                contract.amount_due = int(sum(invoice_lines.mapped("price_subtotal")))

    @api.multi
    def get_gift_communication(self, product):
        self.ensure_one()
        lang = self.mapped(self.send_gifts_to).lang
        child = self.child_id.with_context(lang=lang)
        born = {
            "en_US": "Born in",
            "fr_CH": "Né le" if child.gender == "M" else "Née le",
            "de_DE": "Geburtstag",
            "it_IT": "Compleanno",
        }
        birthdate = child.birthdate.strftime("%d.%m.%Y")
        vals = {
            "firstname": child.preferred_name,
            "local_id": child.local_id,
            "product": product.with_context(lang=lang).name,
            "birthdate": born[lang] + " " + birthdate
            if "Birthday" in product.with_context(lang="en_US").name
            else "",
        }
        if "Birthday" in product.with_context(lang="en_US").name:
            communication = (
                f"{vals['firstname']} ({vals['local_id']})"
                f"<br/>{vals['product']}"
                f"<br/>{vals['birthdate']}"
            )
        else:
            communication = (
                f"{vals['firstname']} ({vals['local_id']})"
                f"<br/>{vals['product']}"
            )
        gift_threshold = self.env['gift.threshold.settings'].search([
            ('product_id', '=', product.id)
        ], limit=1)
        if gift_threshold:
            min = int(gift_threshold.min_amount)
            max = int(gift_threshold.max_amount)
            amount_limit = {
                "en_US": f"CHF {min}.- to max {max}.- per year",
                "fr_CH": f"CHF {min}.- à max. {max}.- par année",
                "de_DE": f"CHF {min}.- bis max. {max}.- pro Jahr",
                "it_IT": f"Importo tra CHF {min}.- e {max}.- per anno",
            }
            communication += f"<br/>{amount_limit[lang]}"
        return communication

    @api.multi
    def generate_bvr_reference(self, product):
        self.ensure_one()
        return self.env["l10n_ch.payment_slip"]._space(
            self.env["generate.gift.wizard"]
                .generate_bvr_reference(self, product)
                .lstrip("0")
        )

    @api.model
    def get_sponsorship_gift_products(self):
        gift_categ_id = self.env.ref("sponsorship_compassion.product_category_gift").id
        return self.env["product.product"].search([("categ_id", "=", gift_categ_id)])
