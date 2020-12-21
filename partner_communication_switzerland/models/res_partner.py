##############################################################################
#
#    Copyright (C) 2016-2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from datetime import date

from odoo import api, models, fields, _

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    """
    Add method to send all planned communication of sponsorships.
    """

    _name = "res.partner"
    _inherit = ["res.partner", "translatable.model"]

    letter_delivery_preference = fields.Selection(
        selection="_get_delivery_preference",
        default="auto_digital",
        required=True,
        help="Delivery preference for Child Letters",
    )
    tax_receipt_preference = fields.Selection(
        selection="_get_delivery_preference",
        compute="_compute_tax_receipt_preference",
        store=True,
    )
    is_new_donor = fields.Boolean(compute="_compute_new_donor")

    @api.multi
    def _compute_salutation(self):
        """ Redefine salutations for Switzerland. """
        # Family shouldn't be used with informal salutation
        family_title = self.env.ref("partner_compassion.res_partner_title_family")
        family = self.filtered(lambda p: p.title == family_title)
        # Special salutation for companies
        company = (self - family).filtered(lambda p: p.is_company or not p.firstname
                                           or not p.title)

        for p in company:
            with api.Environment.manage():
                lang_partner = p.with_context(lang=p.lang)
                p.salutation = lang_partner.get(_("Dear friends of Compassion"))
                p.short_salutation = lang_partner.salutation
                p.informal_salutation = lang_partner.get(_("Dear friend of Compassion"))
                p.full_salutation = lang_partner.salutation

        for partner in family:
            lang_partner = partner.with_context(lang=partner.lang)
            title = lang_partner.title
            title_salutation = (
                lang_partner.env["ir.advanced.translation"]
                .get("salutation", female=title.gender == "F", plural=title.plural)
                .title()
            )
            partner.salutation = (
                title_salutation + " " + title.name + " " + lang_partner.lastname
            )
            partner.short_salutation = lang_partner.salutation
            partner.informal_salutation = lang_partner.salutation
            partner.full_salutation = lang_partner.salutation

        for partner in (self - family - company):
            lang_partner = partner.with_context(lang=partner.lang)
            title = lang_partner.title
            title_salutation = (
                lang_partner.env["ir.advanced.translation"]
                .get("salutation", female=title.gender == "F",
                     plural=title.plural)
                .title()
            )
            title_name = title.name
            partner.salutation = (
                title_salutation + " " + title_name + " " +
                lang_partner.lastname
            )
            pref_name = lang_partner.preferred_name or lang_partner.firstname or \
                lang_partner.name
            partner.short_salutation = title_salutation + " " + pref_name
            partner.informal_salutation = title_salutation + " " + pref_name
            partner.full_salutation = (
                title_salutation + " " + (lang_partner.preferred_name or "") + " " +
                lang_partner.lastname
            )

    @api.multi
    @api.depends("tax_certificate", "birthdate_date")
    def _compute_tax_receipt_preference(self):
        """
        Converts old preference into communication preference.
        """
        receipt_mapping = {
            "no": "none",
            "only_email": "digital_only",
            "paper": "physical",
        }

        def _get_default_pref(partner):
            if partner.birthdate_date:
                today = date.today()
                birthday = partner.birthdate_date
                if (today - birthday).days > 365 * 60:
                    # Old people get paper
                    return "physical"
            return "digital"

        for partner in self:
            partner.tax_receipt_preference = receipt_mapping.get(
                partner.tax_certificate, _get_default_pref(partner)
            )

    @api.multi
    def _compute_new_donor(self):
        invl_obj = self.env["account.invoice.line"].with_context(lang="en_US")
        for partner in self:
            donation_invl = invl_obj.search(
                [
                    ("partner_id", "=", partner.id),
                    ("state", "=", "paid"),
                    ("product_id.categ_name", "!=", "Sponsorship"),
                ]
            )
            payments = donation_invl.mapped("last_payment")
            new_donor = len(payments) < 2 and not partner.has_sponsorships
            partner.is_new_donor = new_donor

    @api.model
    def generate_tax_receipts(self):
        """
        Generate all tax receipts of last year.
        Called once a year to prepare all communications
        :return: recordset of partner.communication.job
        """
        # Select partners that made donations last year
        today = date.today()
        start_date = today.replace(today.year - 1, 1, 1)
        end_date = today.replace(today.year - 1, 12, 31)
        invoice_lines = self.env["account.invoice.line"].search(
            [
                ("last_payment", ">=", start_date),
                ("last_payment", "<=", end_date),
                ("state", "=", "paid"),
                ("product_id.requires_thankyou", "=", True),
                ("partner_id.tax_certificate", "!=", "no"),
            ]
        )
        config = self.env.ref("partner_communication_switzerland." "tax_receipt_config")
        existing_comm = self.env["partner.communication.job"].search(
            [
                ("config_id", "=", config.id),
                ("state", "in", ["pending", "done", "call"]),
                ("date", ">", end_date),
            ]
        )
        partners = invoice_lines.mapped("partner_id") - existing_comm.mapped(
            "partner_id"
        )
        total = len(partners)
        count = 1
        for partner in partners:
            _logger.info(f"Generating tax receipts: {count}/{total}")
            comm_vals = {
                "config_id": config.id,
                "partner_id": partner.id,
                "object_ids": partner.id,
                "user_id": config.user_id.id,
                "show_signature": True,
                "print_subject": False,
            }

            self.env["partner.communication.job"].create(comm_vals)
            donation_amount = partner.get_receipt(today.year - 1)
            email_limit = int(
                self.env["ir.config_parameter"]
                    .sudo()
                    .get_param(
                    "partner_communication_switzerland.tax_receipt_email_limit", "1000"
                )
            )
            if (
                    partner.tax_certificate != "only_email"
                    and donation_amount > email_limit
            ):
                comm_vals["send_mode"] = "physical"
            self.env["partner.communication.job"].create(comm_vals)
            # Commit at each creation of communication to avoid starting all
            # again in case the job failed
            self.env.cr.commit()  # pylint: disable=invalid-commit
            count += 1
        return True

    @api.multi
    def sms_send_step1_confirmation(self, child_request):
        # Override to use a communication instead of message_post
        config = self.env.ref(
            "partner_communication_switzerland.sms_registration_confirmation_1"
        )
        child_request.sponsorship_id.send_communication(config)
        return True

    @api.multi
    def sms_send_step2_confirmation(self, child_request):
        # Override to avoid sending confirmation (handled by regular onboarding process)
        return True

    @api.multi
    def create_odoo_user(self):
        # Override compassion-modules/crm_compassion method
        # add a step on the odoo user creation with a custom wizard
        ctx = {"active_ids": self.ids}
        return {
            "name": _("Create odoo user"),
            "type": "ir.actions.act_window",
            "res_model": "res.partner.create.portal.wizard",
            "view_mode": "form",
            "view_id": self.env.ref(
                "partner_communication_switzerland."
                "res_partner_create_portal_wizard_form"
            ).id,
            "target": "new",
            "context": ctx,
        }
