##############################################################################
#
#    Copyright (C) 2016-2023 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
import logging
import re
from collections import OrderedDict
from datetime import date, datetime
from math import ceil

import requests
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.sponsorship_compassion.models.product_names import GIFT_PRODUCTS_REF

from ..wizards.generate_communication_wizard import SMS_CHAR_LIMIT, SMS_COST

_logger = logging.getLogger(__name__)

try:
    from bs4 import BeautifulSoup
except ImportError:
    _logger.warning("Please install bs4 for using the module")


class PartnerCommunication(models.Model):
    _inherit = "partner.communication.job"

    event_id = fields.Many2one("crm.event.compassion", "Event", readonly=False)
    ambassador_id = fields.Many2one("res.partner", "Ambassador", readonly=False)
    currency_id = fields.Many2one(
        "res.currency", compute="_compute_currency", readonly=False
    )
    sms_cost = fields.Float()
    # sms_provider_id = fields.Many2one(
    #     "sms.provider",
    #     "SMS Provider",
    #     default=lambda self: self.env.ref("sms_939.large_account_id", False),
    #     readonly=False,
    # )

    def schedule_call(self):
        self.ensure_one()
        user_id = self.user_id.id
        sponsorship_reminder_2 = self.env.ref(
            "partner_communication_switzerland.sponsorship_waiting_reminder_2"
        )

        if self.config_id == sponsorship_reminder_2:
            related_contracts = self.get_objects()
            for contract in related_contracts:
                ambassador = contract.origin_id.event_id.user_id
                employee = (
                    self.env["hr.employee"]
                    .sudo()
                    .search([("user_id", "=", ambassador.id)], limit=1)
                )
                # Event ambassador is a church rep
                if employee.job_id.with_context(lang="en_US").name == "Church rep":
                    user_id = ambassador.id

        super(PartnerCommunication, self.with_user(user_id)).schedule_call()

    @api.model
    def send_mode_select(self):
        modes = super().send_mode_select()
        modes.append(("sms", _("SMS")))
        return modes

    def _compute_currency(self):
        chf = self.env.ref("base.CHF")
        for wizard in self:
            wizard.currency_id = chf.id

    def filter_not_read(self):
        """
        Useful for checking if the communication was read by the sponsor.
        Printed letters are always treated as read.
        Returns only the communications that are not read.
        """
        not_read = self.env[self._name]
        # Use a query to improve performance
        query_sql = """
            SELECT DISTINCT m.id
            FROM mail_mail m
            FULL JOIN mail_tracking_email tmail ON tmail.mail_id = m.id
            FULL JOIN mail_tracking_event tevent ON tevent.tracking_email_id = tmail.id
            WHERE m.id = %s
            AND (
                m.state IN ('exception', 'cancel')
                OR tevent.event_type IN (
                    'hard_bounce', 'soft_bounce', 'spam', 'reject')
                OR tmail.state IN (
                    'error', 'rejected', 'spam', 'bounced', 'soft-bounced')
            )
        """
        for communication in self:
            if communication.email_id:
                self.env.cr.execute(query_sql, [communication.email_id.id])
                if self.env.cr.rowcount:
                    not_read += communication
            elif communication.state == "done" and communication.send_mode == "digital":
                not_read += communication
        return not_read

    def get_birthday_bvr(self):
        """
        Attach birthday gift slip with background for sending by e-mail
        :return: dict {attachment_name: [report_name, pdf_data]}
        """
        self.ensure_one()
        attachments = dict()
        background = self.send_mode and "physical" not in self.send_mode
        sponsorships = self.get_objects().filtered(lambda s: not s.birthday_paid)
        gifts_to = sponsorships[:1].gift_partner_id
        if sponsorships and gifts_to == self.partner_id:
            birthday_gift = self.env["product.product"].search(
                [("default_code", "=", GIFT_PRODUCTS_REF[0])], limit=1
            )
            attachments = sponsorships.get_bvr_gift_attachment(
                birthday_gift, background
            )
        return attachments

    def get_graduation_bvr(self):
        """
        Attach graduation gift slip with background for sending by e-mail
        :return: dict {attachment_name: [report_name, pdf_data]}
        """
        self.ensure_one()
        attachments = dict()
        background = self.send_mode and "physical" not in self.send_mode
        sponsorships = self.get_objects()
        graduation = self.env["product.product"].search(
            [("default_code", "=", GIFT_PRODUCTS_REF[4])], limit=1
        )
        gifts_to = sponsorships[0].gift_partner_id
        if sponsorships and gifts_to == self.partner_id:
            attachments = sponsorships.get_bvr_gift_attachment(graduation, background)
        return attachments

    def get_family_slip_attachment(self):
        """
        Attach family gift slip with background for sending by e-mail
        :return: dict {attachment_name: [report_name, pdf_data]}
        """
        self.ensure_one()
        attachments = dict()
        background = self.send_mode and "physical" not in self.send_mode
        sponsorships = self.get_objects()
        family = self.env["product.product"].search(
            [("default_code", "=", GIFT_PRODUCTS_REF[2])], limit=1
        )
        gifts_to = sponsorships[0].gift_partner_id
        if sponsorships and gifts_to == self.partner_id:
            attachments = sponsorships.get_bvr_gift_attachment(family, background)
        return attachments

    def get_all_gift_bvr(self):
        """
        attach all 3 gifts slip with background for sending by e-mail
        :return: dict {attachment_name: [report_name, pdf_data]}
        """
        self.ensure_one()
        attachments = dict()
        background = self.send_mode and "physical" not in self.send_mode
        sponsorships = self.get_objects()
        refs = [GIFT_PRODUCTS_REF[0], GIFT_PRODUCTS_REF[1], GIFT_PRODUCTS_REF[2]]
        all_gifts = self.env["product.product"].search([("default_code", "in", refs)])
        gifts_to = sponsorships[0].gift_partner_id
        if sponsorships and gifts_to == self.partner_id:
            attachments = sponsorships.filtered(
                lambda x: x.state not in ("terminated", "cancelled")
            ).get_bvr_gift_attachment(all_gifts, background)
        return attachments

    def get_fund_bvr(self):
        """
        attach any fund slip with background for sending by e-mail
        :return: dict {attachment_name: [report_name, pdf_data]}
        """
        self.ensure_one()
        background = self.send_mode and "physical" not in self.send_mode
        product = self.config_id.product_id
        data = {
            "product_id": product.id,
            "product_ids": product.ids,
            "background": background,
            "doc_ids": self.partner_id.ids,
        }
        report_name = "report_compassion.bvr_fund"
        pdf = self._get_pdf_from_data(
            data, self.env.ref("report_compassion.report_bvr_fund")
        )
        return {product.name + ".pdf": [report_name, pdf]}

    def get_reminder_bvr(self):
        """
        Attach sponsorship due payment slip with background for sending by
        e-mail.
        :return: dict {attachment_name: [report_name, pdf_data]}
        """
        self.ensure_one()
        sponsorships = self.get_objects()

        payment_mode = sponsorships.with_context(lang="en_US").mapped(
            "payment_mode_id.name"
        )[0]
        # LSV-DD Waiting reminders special case
        if "Waiting Reminder" in self.config_id.name and (
            "LSV" in payment_mode or "Postfinance" in payment_mode
        ):
            if not self.partner_id.bank_ids or not self.partner_id.valid_mandate_id:
                # Don't put payment slip if we just wait the authorization form
                pm = self.env["account.payment.mode"].search(
                    [("name", "=", payment_mode)]
                )
                return {
                    "lsv_form.pdf": [
                        "partner_communication.a4_no_margin",
                        pm.payment_method_id.lsv_form_pdf,
                    ]
                }

        # Put product sponsorship to print the payment slip for physical print.
        if self.send_mode and "physical" in self.send_mode:
            self.product_id = self.env["product.product"].search(
                [("default_code", "=", "sponsorship")], limit=1
            )
            return dict()

        # In other cases, attach the payment slip.
        report_name = "report_compassion.bvr_due"
        data = {
            "background": True,
            "doc_ids": sponsorships.ids,
            "disable_scissors": True,
        }
        pdf = self._get_pdf_from_data(
            data, self.env.ref("report_compassion.report_bvr_due")
        )
        return {_("sponsorship due.pdf"): [report_name, pdf]}

    def get_label_from_sponsorship(self):
        """
        Attach sponsorship labels. Used from communication linked to children.
        :return: dict {attachment_name: [report_name, pdf_data]}
        """
        self.ensure_one()
        sponsorships = self.get_objects()
        return self.get_label_attachment(sponsorships)

    def get_label_attachment(self, sponsorships=False):
        """
        Attach sponsorship labels. Used from communication linked to children.
        :return: dict {attachment_name: [report_name, pdf_data]}
        """
        self.ensure_one()
        if not sponsorships:
            sponsorships = self.env["recurring.contract"]
            children = self.get_objects()
            for child in children:
                sponsorships += child.sponsorship_ids[0]
        attachments = dict()
        report_name = "label.dynamic_label"
        label_data = {
            "doc_ids": sponsorships.ids,
        }
        report = self.env.ref("label.dynamic_label")
        pdf = self._get_pdf_from_data(label_data, report)
        attachments[_("sponsorship labels.pdf")] = [report_name, pdf]
        return attachments

    def get_yearly_payment_slips(self):
        """
        Attach payment slips
        :return: dict {attachment_name: [report_name, pdf_data]}
        """
        self.ensure_one()
        sponsorships = self.get_objects()
        payment_mode_bvr = self.env.ref("sponsorship_switzerland.payment_mode_bvr")
        attachments = dict()
        # IF payment mode is BVR and partner is paying
        # attach sponsorship payment slips
        pay_bvr = sponsorships.filtered(
            lambda s: s.payment_mode_id == payment_mode_bvr
            and s.partner_id == self.partner_id
        )
        if pay_bvr and pay_bvr.must_pay_next_year():
            today = date.today()
            date_start = today.replace(today.year + 1, 1, 1)
            date_stop = date_start.replace(month=12, day=31)
            report_name = "report_compassion.2bvr_sponsorship"
            data = {
                "doc_ids": pay_bvr.ids,
                "date_start": date_start,
                "date_stop": date_stop,
                "background": self.send_mode != "physical",
            }
            pdf = self._get_pdf_from_data(
                data, self.env.ref("report_compassion.report_2bvr_sponsorship")
            )
            attachments.update({_("sponsorship payment slips.pdf"): [report_name, pdf]})
        # Attach gifts for correspondents
        pays_gift = self.env["recurring.contract"]
        for sponsorship in sponsorships:
            if sponsorship.mapped(sponsorship.send_gifts_to) == self.partner_id:
                pays_gift += sponsorship
        if pays_gift:
            product_ids = (
                self.env["product.product"]
                .search(
                    [
                        (
                            "default_code",
                            "in",
                            [GIFT_PRODUCTS_REF[0]] + GIFT_PRODUCTS_REF[2:4],
                        )
                    ]
                )
                .ids
            )
            report_name = "report_compassion.2bvr_gift_sponsorship"
            data = {"doc_ids": pays_gift.ids, "product_ids": product_ids}
            pdf = self._get_pdf_from_data(
                data,
                self.env.ref("report_compassion.report_2bvr_gift_sponsorship"),
            )
            attachments.update({_("sponsorship gifts.pdf"): [report_name, pdf]})
        return attachments

    def get_photo_by_post_attachment(self):
        self.ensure_one()
        attachments = self.get_child_picture_attachment()
        # Add a blank page for printing the address
        attachments.update(self.get_blank_communication_attachment())
        return attachments

    def get_blank_communication_attachment(self):
        blank_communication = self._get_pdf_from_data(
            {"doc_ids": self.ids},
            self.env.ref("report_compassion.report_blank_communication"),
        )
        return {
            "cover.pdf": ["report_compassion.blank_communication", blank_communication]
        }

    def get_childpack_attachment(self):
        self.ensure_one()
        lang = self.partner_id.lang
        sponsorships = self.get_objects()
        children = sponsorships.mapped("child_id")
        report_name = "report_compassion.childpack_small"
        data = {
            "lang": lang,
            "is_pdf": self.send_mode != "physical",
            "type": report_name,
            "doc_ids": children.ids,
        }
        pdf = self._get_pdf_from_data(
            data, self.sudo().env.ref("report_compassion.report_childpack_small")
        )
        return {_("child dossier.pdf"): [report_name, pdf]}

    def get_end_sponsorship_certificate_new_version(self):
        return self.get_end_sponsorship_certificate(new_version=True)

    def get_end_sponsorship_certificate(self, new_version=False):
        self.ensure_one()
        lang = self.partner_id.lang
        sponsorships = self.get_objects()
        report_name = "report_compassion.ending_sponsorship_certificate"
        data = {
            "lang": lang,
            "digital": self.send_mode != "physical",
            "doc_ids": sponsorships.ids,
            "long_lasting": max(sponsorships.mapped("contract_duration")) >= 730,
            "new_version": new_version,
        }
        pdf = self._get_pdf_from_data(
            data,
            self.sudo().env.ref(
                "report_compassion.report_ending_sponsorship_certificate"
            ),
        )
        return {_("ending sponsorship certificate.pdf"): [report_name, pdf]}

    def get_tax_receipt(self):
        self.ensure_one()
        report_name = "report_compassion.tax_receipt"
        data = {
            "doc_ids": self.partner_id.ids,
            "year": self.env.context.get("year", date.today().year - 1),
            "lang": self.partner_id.lang,
        }
        pdf = self._get_pdf_from_data(
            data, self.env.ref("report_compassion.tax_receipt_report")
        )
        return {_("tax receipt.pdf"): [report_name, pdf]}

    def send(self):
        """
        Sends communication jobs, handling various functionalities:

        - Mark B2S correspondence as read when printed.
        - Postpone no money holds when reminders sent.
        - Update donor tag
        - Send SMS for sms send_mode
        - Add to zoom session when zoom invitation is sent
        - Set onboarding_start_date when first communication is sent
        - Start onboarding new donor after first thank you letter is sent
        - Prepare SUB validation after SUB proposal is sent

        Returns:
            True
        """
        # Filter jobs for SMS
        sms_jobs = self.filtered(lambda j: j.send_mode == "sms")
        sms_jobs.send_by_sms()

        # Filter remaining jobs and contract channel
        other_jobs = self - sms_jobs

        # Handle invoice reconciliation conflicts
        if not other_jobs._handle_invoice_reconciliation():
            raise UserError(
                _(
                    "Some invoices are being reconciled. Please wait before sending "
                    "the communication."
                )
            )

        # Prevent sending onboarding card with unverified partners
        if not other_jobs._check_onboarding_verification():
            raise UserError(
                _("Onboarding postcard cannot be sent for unverified partners.")
            )

        # Send remaining jobs
        super(PartnerCommunication, other_jobs).send()

        other_jobs._handle_no_money_holds()
        other_jobs._start_new_donors_onboarding()
        other_jobs._handle_zoom_and_sub_proposal()
        self._prepare_onboarding()

        return True

    # Helper functions for improved readability and modularity
    def _handle_invoice_reconciliation(self):
        contract_channel = self.env.ref("recurring_contract.channel_recurring_contract")
        for communication in self.filtered(
            lambda j: j.model in ("recurring.contract", "account.move")
        ):
            queue_job = self.env["queue.job"].search(
                [
                    ("job_function_id.channel_id", "=", contract_channel.id),
                    ("state", "!=", "done"),
                ],
                limit=1,
            )
            if queue_job:
                invoices = self.env["account.move"].browse(queue_job.record_ids)
                if communication.partner_id in invoices.mapped("partner_id"):
                    return False
        return True

    def _check_onboarding_verification(self):
        """
        Checks if any jobs in the provided list are for sending the onboarding postcard
        and the corresponding partner is not yet verified.
        """
        onboarding_card = self.env.ref(
            "partner_communication_switzerland"
            ".config_new_donors_onboarding_postcard_and_magazine"
        )
        verify_activity = self.env.ref("partner_auto_match.activity_check_duplicates")

        # Filter jobs for onboarding postcard and unverified partners
        unverified_jobs = self.filtered(
            lambda j: j.config_id == onboarding_card
            and j.partner_id.activity_ids.filtered(
                lambda a: a.activity_type_id == verify_activity
            )
        )
        return not unverified_jobs

    def _handle_no_money_holds(self):
        """
        Extends the expiration date of no money holds based on configured settings
        for jobs related to corresponding communication templates.
        """
        settings = self.env["res.config.settings"].sudo()
        first_extension = settings.get_param("no_money_hold_duration")
        second_extension = settings.get_param("no_money_hold_extension")

        # Define template references for no money holds
        no_money_1 = self.env.ref(
            "partner_communication_switzerland.sponsorship_waiting_reminder_1"
        )
        no_money_2 = self.env.ref(
            "partner_communication_switzerland.sponsorship_waiting_reminder_2"
        )
        no_money_3 = self.env.ref(
            "partner_communication_switzerland.sponsorship_waiting_reminder_3"
        )

        for communication in self:
            extension_days = 0

            # Determine extension based on communication template
            if communication.config_id == no_money_1:
                extension_days = first_extension + 7
            elif communication.config_id == no_money_2:
                extension_days = second_extension + 7
            elif communication.config_id == no_money_3:
                extension_days = 10

            # Apply extension if applicable
            if extension_days:
                holds = communication.get_objects().mapped("child_id.hold_id")
                for hold in holds:
                    hold.expiration_date = datetime.now() + relativedelta(
                        days=extension_days
                    )

    def _start_new_donors_onboarding(self):
        """
        Starts the onboarding process for new donors identified from thank you letters.
        """

        new_donor_template_field = "thankyou_preference"
        invoice_line_model = "account.invoice.line"

        # Filter jobs for thank you letters sent to new donors
        new_donor_jobs = self.filtered(
            lambda j: j.config_id.model == invoice_line_model
            and j.config_id.send_mode_pref_field == new_donor_template_field
        )

        # Extract and filter partner records for new donors
        new_donor_partners = new_donor_jobs.mapped(
            "partner_id"
        ).filter_onboarding_new_donors()

        # Start onboarding for the identified new donors
        new_donor_partners.start_new_donors_onboarding()

    def _handle_zoom_and_sub_proposal(self):
        """
        Handles two functionalities:
            - Adds partners to Zoom sessions for jobs related to the onboarding
            invitation.
            - Updates the SUB proposal date for jobs related to the SUB proposal
            template.
        """

        # Zoom session reference
        zoom_invitation = self.env.ref(
            "partner_communication_switzerland.config_onboarding_step1"
        )

        # Handle adding partners to Zoom sessions
        for invitation in self.filtered(
            lambda j: j.config_id == zoom_invitation
            and j.get_objects().filtered("is_first_sponsorship")
        ):
            next_zoom = (
                self.env["res.partner.zoom.session"]
                .with_context(lang=invitation.partner_id.lang)
                .get_next_session()
            )
            if next_zoom:
                next_zoom.add_participant(invitation.partner_id)

        # SUB proposal reference
        sub_proposal = self.env.ref(
            "partner_communication_switzerland.planned_sub_dossier"
        )

        # Update SUB proposal date for relevant jobs
        subs = self.filtered(lambda j: j.config_id == sub_proposal)
        if subs:
            subs.get_objects().write({"sub_proposal_date": fields.Date.today()})

    def _prepare_onboarding(self):
        """
        Prepares onboarding for new sponsors identified from communication:
            - Sets the onboarding start date for the first communication sent.
            - Prepares the signup URL for new sponsors.

        Args:
            jobs: List of communication jobs.
        """

        welcome_onboarding = self.env.ref(
            "partner_communication_switzerland"
            ".config_onboarding_sponsorship_confirmation"
        )
        wrpr_onboarding = self.env.ref(
            "partner_communication_switzerland.config_wrpr_welcome"
        )

        # Filter relevant welcome communication jobs for new sponsors
        welcome_comms = self.filtered(
            lambda j: j.config_id in (welcome_onboarding + wrpr_onboarding)
            and j.get_objects().filtered("is_first_sponsorship")
        )

        if welcome_comms:
            # Prepare MyCompassion Account
            _logger.info("Prepare signup URL for new sponsor")
            welcome_comms.mapped("partner_id").action_signup_prepare()
            # Set onboarding start date for identified new sponsors
            welcome_comms.get_objects().write(
                {"onboarding_start_date": datetime.today()}
            )

    def send_by_sms(self):
        """
        Sends communication jobs with SMS 939 service.
        :return: list of sms_texts
        """
        link_pattern = re.compile(r'<a href="([^<>]*)">([^<]*)</a>')
        sms_medium_id = self.env.ref("sms_sponsorship.utm_medium_sms").id
        sms_texts = []
        for job in self.filtered(lambda j: j.state == "pending" and j.partner_mobile):
            sms_text = job.convert_html_for_sms(link_pattern, sms_medium_id)
            sms_texts.append(sms_text)
            job.partner_id.with_context(
                sms_provider=job.sms_provider_id
            ).message_post_send_sms(sms_text, note_msg=job.subject)
            job.write(
                {
                    "state": "done",
                    "sent_date": fields.Datetime.now(),
                    "sms_cost": ceil(float(len(sms_text)) // SMS_CHAR_LIMIT) * SMS_COST,
                }
            )
            _logger.debug("SMS length: %s", len(sms_text))
        return sms_texts

    def convert_html_for_sms(self, link_pattern, sms_medium_id):
        """
        Converts HTML into simple text for SMS.
        First replace links with short links using Link Tracker.
        Then clean HTML using BeautifulSoup library.
        :param link_pattern: the regex pattern for replacing links
        :param sms_medium_id: the associated utm.medium id for generated links
        :return: Clean text with short links for SMS use.
        """
        self.ensure_one()
        source_id = self.config_id.source_id.id
        paragraph_delimiter = "###P###"

        def _replace_link(match):
            full_link = match.group(1).replace("&amp;", "&")
            short_link = self.env["link.tracker"].search(
                [
                    ("url", "=", full_link),
                    ("source_id", "=", source_id),
                    ("medium_id", "=", sms_medium_id),
                ]
            )
            if not short_link:
                short_link = self.env["link.tracker"].create(
                    {
                        "url": full_link,
                        "campaign_id": self.utm_campaign_id.id
                        or self.env.ref(
                            "partner_communication_compassion."
                            "utm_campaign_communication"
                        ).id,
                        "medium_id": sms_medium_id,
                        "source_id": source_id,
                    }
                )
            return short_link.short_url

        body = self.body_html.replace("\n", " ").replace(
            "</p>", "</p>" + paragraph_delimiter
        )
        body = link_pattern.sub(_replace_link, body)
        body = re.sub(r"[ \t\r\f\v]+", " ", body)
        body = re.sub(r"<br>|<br/>", "\n", body)
        soup = BeautifulSoup(body, "lxml")
        text = soup.get_text().replace(paragraph_delimiter, "\n\n")
        return "\n".join([t.strip() for t in text.split("\n")])

    def get_print_dossier_attachments(self):
        """
        Returns pdfs for the Printed New Dossier Communication, including:
        - Sponsorship payment slips (if payment is True)
        - Small Childpack
        - Sponsorship labels
        - Child picture
        :return: dict {attachment_name: [report_name, pdf_data]}
        """
        self.ensure_one()
        attachments = self.get_sponsorship_payment_slip_attachments()
        attachments.update(self.get_childpack_attachment())
        write_sponsorships = self.get_objects().filtered(
            lambda s: s.correspondent_id == self.partner_id
        )
        if write_sponsorships and self.send_mode == "physical":
            attachments.update(self.get_label_attachment(write_sponsorships))

        # Child picture
        attachments.update(self.get_child_picture_attachment())

        return attachments

    def get_contract_payment_slip_a4(self):
        self.ensure_one()
        return self.get_sponsorship_payment_slip_attachments(
            force_a4=self.send_mode == "physical"
        )

    def get_sponsorship_payment_slip_attachments(self, force_a4=False):
        self.ensure_one()
        account_payment_mode_obj = self.env["account.payment.mode"].with_context(
            lang="en_US"
        )
        lsv_dd_modes = account_payment_mode_obj.search(
            ["|", ("name", "like", "Direct Debit"), ("name", "like", "LSV")]
        )
        permanent_order = self.env.ref(
            "sponsorship_switzerland.payment_mode_permanent_order"
        )
        bvr = self.env.ref("sponsorship_switzerland.payment_mode_bvr")

        sponsorships = self.get_objects()
        # Sponsorships included for payment slips
        bv_sponsorships = sponsorships.filtered(
            # 1. Needs to be payer
            lambda s: s.partner_id == self.partner_id
            and
            # 2. Permanent Order/BVR are always included
            s.payment_mode_id in (permanent_order, bvr)
            # The sponsorship amount must be set
            and s.total_amount
            # 3. LSV/DD are never included
            and s.payment_mode_id not in lsv_dd_modes
            # 4. If already paid they are not included
            and not s.period_paid
        )

        # Include all active sponsorships for Permanent Order
        bv_sponsorships |= (
            sponsorships.filtered(
                lambda s: s.partner_id == self.partner_id
                and s.payment_mode_id == permanent_order
            )
            .mapped("group_id.contract_ids")
            .filtered(lambda s: s.state in ("active", "waiting"))
        )

        attachments = {}
        # Payment slips
        if bv_sponsorships:
            report_name = "report_compassion.2bvr_sponsorship"
            report_ref = self.env.ref("report_compassion.report_2bvr_sponsorship")
            if (
                bv_sponsorships.mapped("payment_mode_id") == permanent_order
                and not force_a4
            ):
                # One single slip is enough for permanent order.
                report_name = "report_compassion.single_bvr_sponsorship"
                report_ref = self.env.ref(
                    "report_compassion.report_single_bvr_sponsorship"
                )
            data = {
                "doc_ids": bv_sponsorships.ids,
                "background": self.send_mode != "physical",
            }
            pdf = self._get_pdf_from_data(data, report_ref)
            attachments.update({_("sponsorship payment slips.pdf"): [report_name, pdf]})

        lsv_dd_sponsorships = sponsorships.filtered(
            lambda s: s.payment_mode_id in lsv_dd_modes
        )
        if lsv_dd_sponsorships and not self.partner_id.valid_mandate_id:
            lang = self.env.lang[:2].upper() if self.env.lang != "en_US" else "DE"
            pdf_form = base64.b64encode(
                requests.get(
                    f"https://compassion.ch/wp-content/uploads/documents_compassion/"
                    f"Formulaire_LSV_DD_{lang}.pdf"
                ).content
            )
            attachments.update(
                {
                    _("bank authorization form.pdf"): [
                        "partner_communication.a4_no_margin",
                        pdf_form,
                    ]
                }
            )
        return attachments

    def get_csp_picture(self):
        self.ensure_one()
        field_offices = set(
            self.get_objects().mapped(
                "contract_line_ids.product_id.survival_sponsorship_field_office_id"
            )
        )
        attachments = {}
        data_name = "partner_communication_switzerland.report_csp_picture"
        report_name = "partner_communication_switzerland.csp_picture"
        for field_office in field_offices:
            pdf_data = self._get_pdf_from_data(
                {"FO": field_office.field_office_id, "doc_ids": self.ids},
                self.env.ref(data_name),
            )
            attachments.update({field_office.name + ".pdf": [report_name, pdf_data]})
        return attachments

    def get_csp_attachment(self):
        self.ensure_one()
        attachments = OrderedDict()
        account_payment_mode_obj = self.env["account.payment.mode"]
        csp = self.get_objects()

        # Include all active csp for Permanent Order
        if "Permanent Order" in csp.with_context(lang="en_US").mapped(
            "payment_mode_id.name"
        ):
            csp += csp.mapped("group_id.contract_ids").filtered(
                lambda s: s.state == "active"
            )

        is_payer = self.partner_id in csp.mapped("partner_id")
        make_payment_pdf = True

        # LSV/DD don't need a payment slip
        groups = csp.mapped("group_id")
        lsv_dd_modes = account_payment_mode_obj.search(
            ["|", ("name", "like", "Direct Debit"), ("name", "like", "LSV")]
        )
        lsv_dd_groups = groups.filtered(lambda r: r.payment_mode_id in lsv_dd_modes)
        if len(lsv_dd_groups) == len(groups):
            make_payment_pdf = False

        # If partner already paid, avoid payment slip
        if len(csp.filtered("period_paid")) == len(csp):
            make_payment_pdf = False

        # Payment slips
        if is_payer and make_payment_pdf:
            report_name = "report_compassion.2bvr_sponsorship"
            data = {"doc_ids": csp.ids}
            pdf = self._get_pdf_from_data(
                data, self.env.ref("report_compassion.report_2bvr_sponsorship")
            )
            attachments.update({_("csp payment slips.pdf"): [report_name, pdf]})
        return attachments

    def get_third_party_letters(self):
        """
        Get the third party letters stored in Odoo's attachments table
        """
        self.ensure_one()
        res = {}
        field_offices = set(
            self.get_objects().mapped("child_id.field_office_id.field_office_id")
        )
        lang = self.partner_id.lang[:2]
        for fo in field_offices:
            attachment = (
                self.env["ir.attachment"]
                .with_context(bin_size=False)
                .search([("name", "like", f"TP_{fo}_{lang}.pdf")], limit=1)
            )
            if attachment:
                self.env["partner.communication.attachment"].create(
                    {
                        "name": attachment.name,
                        "communication_id": self.id,
                        "report_id": attachment.report_id.id,
                        "report_name": attachment.report_id.report_name,
                        "attachment_id": attachment.id,
                    }
                )
        return res
