##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from odoo import api, models, fields
from werkzeug.utils import escape

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    """ Add mailing origin in invoice objects. """

    _inherit = "account.invoice"

    @api.model
    def process_wp_confirmed_donation(self, donnation_infos):
        """
        Utility to process the donation done via wordpress.
        :return:
        """
        for key in donnation_infos:
            donnation_infos[key] = escape(donnation_infos[key])

        match_obj = self.env["res.partner.match.wp"]

        # Extract the partner infos
        partner_fields = {  # wp_field : odoo_field
            "email": "email",
            "name": "name",
            "street": "street",
            "zipcode": "zip",
            "city": "city",
            "language": "lang",
            "partner_ref": "ref",
        }
        partner_infos = {"company_id": self.env.user.company_id.id}
        for wp_field, odoo_field in list(partner_fields.items()):
            partner_infos[odoo_field] = donnation_infos[wp_field]

        # Find the matching odoo country
        partner_infos["country_id"] = match_obj.match_country(
            donnation_infos["country"], partner_infos["lang"]
        ).id

        # Find matching partner
        partner = match_obj.match_partner_to_infos(partner_infos)

        # Insert the donation details to the database.
        pf_brand = donnation_infos["pf_brand"]
        pf_pm = donnation_infos["pf_pm"]
        if pf_brand != pf_pm:
            payment_mode = "{}_{}".format(pf_brand, pf_pm)
        else:
            payment_mode = pf_brand

        return self.create_from_wordpress(
            partner.id,
            donnation_infos["orderid"],
            donnation_infos["amount"],
            donnation_infos["fund"],
            donnation_infos["child_id"],
            donnation_infos["pf_payid"],
            payment_mode.strip(),
            donnation_infos["utm_source"],
            donnation_infos["utm_medium"],
            donnation_infos["utm_campaign"],
            donnation_infos["time"]
        )

    @api.model
    def create_from_wordpress(
            self,
            partner_id,
            wp_origin,
            amount,
            fund,
            child_code,
            pf_payid,
            payment_mode_name,
            utm_source,
            utm_medium,
            utm_campaign,
            time
    ):
        """
         Utility for invoice donation creation.
        :param partner_id: odoo partner_id
        :param wp_origin: the fund code in wordpress
        :param amount: amount of donation
        :param fund: the fund code in wordpress
        :param child_code: child local_id
        :param pf_payid: postfinance transaction number
        :param payment_mode_name: the payment_mode identifier from postfinance
        :param utm_source: the utm identifier in wordpress
        :param utm_medium: the utm identifier in wordpress
        :param utm_campaign: the utm identifier in wordpress
        :param time: datetime of donation
        :return: invoice_id
        """
        _logger.info(
            "New donation of CHF %s from Wordpress for partner %s and child %s",
            amount,
            partner_id,
            child_code,
        )
        partner = self.env["res.partner"].browse(partner_id)
        if partner.contact_type == "attached":
            if partner.type == "email_alias":
                # In this case we want to link to the main partner
                partner = partner.contact_id
                partner_id = partner.id
            else:
                # We unarchive the partner to make it visible
                partner.write({"active": True, "contact_id": False})
        product = self.env["product.product"]
        if fund:
            product = product.search([("default_code", "ilike", fund)])
        sponsorship = self.env["recurring.contract"]
        if child_code:
            sponsorship = sponsorship.search(
                [
                    "|",
                    ("partner_id", "=", partner_id),
                    ("correspondent_id", "=", partner_id),
                    ("child_code", "=", child_code),
                ],
                order="id desc",
                limit=1,
            )
        payment_mode = self.env["account.payment.mode"].search(
            [("name", "=", payment_mode_name), ("active", "=", True)]
        )
        if not payment_mode:
            # Credit Card Journal
            journal = self.env["account.journal"].search(
                [("code", "=", "CCRED"), ("company_id", "=", partner.company_id.id), ],
                limit=1,
            )
            payment_mode.create(
                {
                    "name": payment_mode_name,
                    "payment_method_id": 1,  # Manual inbound
                    "payment_type": "inbound",
                    "bank_account_link": "fixed",
                    "fixed_journal_id": journal.id,
                    "active": True,
                }
            )
        origin = "WP " + wp_origin + " " + str(pf_payid)
        utms = self.env["utm.mixin"].get_utms(utm_source, utm_medium, utm_campaign)
        internet_id = self.env.ref("utm.utm_medium_website").id
        payment_term_id = self.env.ref("account.account_payment_term_immediate").id
        account = self.env["account.account"].search([("code", "=", "1050")])
        invoice = self.create(
            {
                "partner_id": partner_id,
                "payment_mode_id": payment_mode.id,
                "origin": origin,
                "reference": str(pf_payid),
                "transaction_id": str(pf_payid),
                "date_invoice": fields.Date.from_string(time),
                "currency_id": 6,  # Always in CHF
                "account_id": account.id,
                "name": "Postfinance payment " + str(pf_payid) + " for " + wp_origin,
                "payment_term_id": payment_term_id,
            }
        )
        analytic_id = (
            self.env["account.analytic.default"].account_get(product.id).analytic_id.id
        )
        analytic_tag_ids = (
            self.env["account.analytic.default"].account_get(product.id
                                                             ).analytic_tag_ids.ids
        )
        gift_account = self.env["account.account"].search([("code", "=", "6003")])
        self.env["account.invoice.line"].create(
            {
                "invoice_id": invoice.id,
                "product_id": product.id,
                "account_id": product.property_account_income_id.id or gift_account.id,
                "contract_id": sponsorship.id,
                "name": product.name or "Online donation for " + wp_origin,
                "quantity": 1,
                "price_unit": amount,
                "account_analytic_id": analytic_id,
                "analytic_tag_ids": [(6, 0, analytic_tag_ids)],
                "source_id": utms["source"],
                "medium_id": utms.get("medium", internet_id),
                "campaign_id": utms["campaign"],
            }
        )
        partner.set_privacy_statement(origin="new_gift")
        invoice.action_invoice_open()
        payment_vals = {
            "journal_id": self.env["account.journal"]
            .search(
                [("name", "=", "Web"), ("company_id", "=", partner.company_id.id)]
            )
            .id,
            "payment_method_id": self.env["account.payment.method"]
            .search([("code", "=", "sepa_direct_debit")])
            .id,
            "payment_date": invoice.date,
            "communication": invoice.reference,
            "invoice_ids": [(6, 0, invoice.ids)],
            "payment_type": "inbound",
            "amount": invoice.amount_total,
            "currency_id": invoice.currency_id.id,
            "partner_id": invoice.partner_id.id,
            "partner_type": "customer",
            "payment_difference_handling": "reconcile",
            "payment_difference": invoice.amount_total,
        }
        account_payment = self.env["account.payment"].create(payment_vals)
        account_payment.post()
        return invoice.id
