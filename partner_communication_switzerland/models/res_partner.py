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
import uuid

from odoo import api, models, fields, _
from odoo.addons.auth_signup.models.res_partner import now

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    """
    Add method to send all planned communication of sponsorships.
    """

    _name = "res.partner"
    _inherit = ["res.partner", "translatable.model"]

    tax_receipt_preference = fields.Selection(
        selection="_get_delivery_preference",
        compute="_compute_tax_receipt_preference",
        store=True,
    )
    letter_delivery_preference = fields.Selection(
        selection="_get_delivery_preference",
        default="auto_digital",
        required=True,
        help="Delivery preference for Child Letters",
    )
    no_physical_letter = fields.Boolean(
        compute="_compute_no_physical_letter",
        inverse="_inverse_no_physical_letter",
        help="Tells if all communication preferences are set to email only.")
    is_new_donor = fields.Boolean(compute="_compute_new_donor")
    last_completed_tax_receipt = fields.Integer(
        compute="_compute_last_completed_tax_receipt",
        help="Gives the year of the last tax receipt sent to the partner"
    )
    informal_salutation = fields.Char(compute="_compute_informal_salutation",
                                      help="Informal salutation used in French")

    onboarding_new_donor_start_date = fields.Date(help="Indicates when the first email of "
                                                       "the new donor onboarding process was sent.",
                                                  copy=False)
    onboarding_new_donor_hash = fields.Char()

    def _get_salutation_fr_CH(self, informal=False):
        self.ensure_one()
        family_title = self.env.ref("partner_compassion.res_partner_title_family")
        friends_title = self.env.ref("partner_compassion.res_partner_title_friends")
        title = self.title
        is_company = self.is_company or not self.firstname or not title or title == friends_title
        if title == family_title:
            return f"Chère famille {self.lastname}"
        elif is_company:
            return "Chers amis de Compassion"
        else:
            cher = self.env["ir.advanced.translation"].get(
                "salutation", female=title.gender == "F", plural=title.plural).title()
            if title.plural:
                if informal:
                    return f"{cher} {self.lastname}"
                else:
                    return f"{cher} {title.name} {self.lastname}"
            else:
                if informal:
                    return f"{cher} {self.firstname}"
                else:
                    return f"{cher} {self.firstname} {self.lastname}"

    def _get_salutation_de_DE(self):
        self.ensure_one()
        family_title = self.env.ref("partner_compassion.res_partner_title_family")
        mister_madam_title = self.env.ref("partner_compassion.res_partner_title_mister_miss")
        friends_title = self.env.ref("partner_compassion.res_partner_title_friends")
        title = self.title
        is_company = self.is_company or not self.firstname or not title or title == friends_title
        if title == family_title:
            return f"Liebe Familie {self.lastname}"
        elif title == mister_madam_title:
            return f"Hallo {self.firstname}"
        elif is_company:
            return "Liebe Freundinnen und Freunde von Compassion"
        else:
            liebe = self.env["ir.advanced.translation"].get(
                "salutation", female=title.gender == "F").title()
            return f"{liebe} {self.firstname}"

    def _get_salutation_it_IT(self):
        self.ensure_one()
        family_title = self.env.ref("partner_compassion.res_partner_title_family")
        title = self.title
        friends_title = self.env.ref("partner_compassion.res_partner_title_friends")
        is_company = self.is_company or not self.firstname or not title or title == friends_title
        if title == family_title:
            return f"Cara Famiglia {self.lastname}"
        elif is_company:
            return "Cari Amici di Compassion"
        else:
            cari = self.env["ir.advanced.translation"].get(
                "salutation", female=title.gender == "F", plural=title.plural).title()
            return f"{cari} {self.firstname}"

    def _compute_informal_salutation(self):
        for partner in self:
            if partner.lang != "fr_CH":
                partner.informal_salutation = partner.salutation
            else:
                lang_partner = partner.with_context(lang=partner.lang)
                partner.informal_salutation = lang_partner._get_salutation_fr_CH(
                    informal=True)

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

    def _compute_no_physical_letter(self):
        for partner in self:
            partner.no_physical_letter = (
                 "only" in partner.global_communication_delivery_preference
                 or partner.global_communication_delivery_preference == "none"
            ) and (
                 "only" in partner.letter_delivery_preference
                 or partner.letter_delivery_preference == "none"
            ) and (
                 "only" in partner.photo_delivery_preference
                 or partner.photo_delivery_preference == "none"
            ) and (
                 "only" in partner.thankyou_preference
                 or partner.thankyou_preference == "none"
            ) and partner.tax_certificate != "paper" and partner.nbmag in (
             "email", "no_mag")

    def _inverse_no_physical_letter(self):
        for partner in self:
            partner.compute_inverse_no_physical_letter()

    def compute_inverse_no_physical_letter(self):
        self.ensure_one()
        no_physical_letters = self.env.context.get("no_physical_letters", self.no_physical_letter)
        if no_physical_letters:
            vals = {
                "nbmag": "no_mag" if self.nbmag == "no_mag" else "email",
                "tax_certificate": "no"
                if self.tax_certificate == "no" else "only_email",
                "calendar": False,
                "sponsorship_anniversary_card": False
            }
            for _field in ["global_communication_delivery_preference",
                           "letter_delivery_preference",
                           "photo_delivery_preference",
                           "thankyou_preference"]:
                value = getattr(self, _field)
                if "auto" in value or value == "both":
                    vals[_field] = "auto_digital_only"
                elif value in ["physical", "digital"]:
                    vals[_field] = "digital_only"
            self.write(vals)
        else:
            vals = {
                "calendar": True,
                "sponsorship_anniversary_card": True
            }
            for _field in ["global_communication_delivery_preference",
                           "letter_delivery_preference",
                           "photo_delivery_preference",
                           "thankyou_preference"]:
                value = getattr(self, _field)
                if "only" in value:
                    vals[_field] = value.replace("_only", "")
            if self.nbmag == "no_mag":
                vals["nbmag"] = "one"
            if self.tax_certificate == "only_email":
                vals["tax_certificate"] = "default"
            self.write(vals)

    def _compute_last_completed_tax_receipt(self):
        for partner in self:
            last_tax_receipt = self.env["partner.communication.job"].search([
                ("config_id", "=", self.env.ref(
                    "partner_communication_switzerland.tax_receipt_config").id),
                ("partner_id", "=", partner.id),
                ("state", "=", "done")
            ], limit=1)
            if last_tax_receipt.date:
                partner.last_completed_tax_receipt = last_tax_receipt.date.year - 1
            else:
                partner.last_completed_tax_receipt = 1979

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
        config = self.env.ref("partner_communication_switzerland.tax_receipt_config")
        existing_comm = self.env["partner.communication.job"].search(
            [
                ("config_id", "=", config.id),
                ("state", "in", ["pending", "done", "call"]),
                ("date", ">", end_date),
            ]
        )
        partners = invoice_lines.mapped("partner_id.commercial_partner_id") - existing_comm.mapped(
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

    def action_reset_password(self):
        """
        Action to change partner's password from backend.
        generate a token and start a communication. The
        communication is not sent automatically but rather
        shown to the backend user once created.
        :return: a redirection to communication job form
        """

        # handle on reset at a time to allow redirection to work properly
        self.ensure_one()

        # use signup prepare to generate a token valid 1 day for password reset
        expiration = now(days=+1)
        self.sudo().signup_prepare(
            signup_type="reset", expiration=expiration
        )

        # create but does not send the communication for password reset
        config = self.env.ref(
            "partner_communication_switzerland.reset_password_email"
        )
        comm = self.env["partner.communication.job"].create(
            {
                "partner_id": self.id,
                "config_id": config.id,
                "auto_send": False,
            }
        )

        # redirect the backend user to the newly created communication.
        return {
            "type": "ir.actions.act_window",
            "name": "Reset Password",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "partner.communication.job",
            "res_id": comm.id,
            "target": "current",
        }

    @api.multi
    def filter_onboarding_new_donors(self):
        return self.filtered(
            lambda p: p.is_new_donor and not p.is_church and not p.sponsorship_ids
            and p.lang != "en_US" and not p.opt_out
        )

    def start_new_donors_onboarding(self):
        config = self.env.ref(
            "partner_communication_switzerland"
            ".config_new_donors_onboarding_postcard_and_magazine"
        )
        for partner in self:
            self.env["partner.communication.job"].create(
                {
                    "partner_id": partner.id,
                    "config_id": config.id,
                    "auto_send": False,
                })

            partner.onboarding_new_donor_start_date = fields.Date.today()
            partner.onboarding_new_donor_hash = uuid.uuid4()

    @api.multi
    def get_base_url(self):
        """Get the base URL for the current partner."""
        self.ensure_one()
        if not self.user_ids or any(self.mapped("user_ids.share")):
            return self.env["ir.config_parameter"].sudo().get_param("web.external.url")
        else:
            return super().get_base_url()
