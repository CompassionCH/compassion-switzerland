##############################################################################
#
#    Copyright (C) 2016-2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
import logging
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models

from odoo.addons.sponsorship_compassion.models.contracts import SPONSORSHIP_TYPE_LIST

logger = logging.getLogger(__name__)


class RecurringContract(models.Model):
    """
    Add method to send all planned communication of sponsorships.
    """

    _inherit = "recurring.contract"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    birthday_paid = fields.Many2many(
        "sponsorship.gift", compute="_compute_birthday_paid", readonly=False
    )
    origin_type = fields.Selection(related="origin_id.type")
    origin_name = fields.Char(related="origin_id.name")
    onboarding_start_date = fields.Date(
        help="Indicates when the first email of " "the onboarding process was sent.",
        copy=False,
    )
    sub_proposal_date = fields.Date(
        help="Trigger for automatic SUB sponsorship validation after 2 weeks"
    )

    @api.onchange("type")
    def _create_empty_lines_for_correspondence(self):
        super()._create_empty_lines_for_correspondence()
        if self.type == "SWP" and not self.correspondent_id.mobile:
            return {
                "warning": {
                    "title": "Write&Pray",
                    "message": "The correspondent doesn't have a mobile phone set. "
                    "Please check this otherwise he or she won't receive "
                    "the communications by SMS.",
                }
            }
        if self.type == "SWP" and not self.correspondent_id.is_young:
            return {
                "warning": {
                    "title": "Write&Pray",
                    "message": "The correspondent is not a young person. "
                    "Please check that this sponsorship is indeed a "
                    "Write&Pray, or use the 'Correspondence' type otherwise.",
                }
            }

    def get_payment_type_attachment_string(self):
        payment_mode = (
            self.with_context(lang="en_US").mapped("payment_mode_id")[:1].name
        )
        if payment_mode == "Permanent Order":
            total_paid = self.mapped("group_id.contract_ids").filtered(
                lambda s: s.state not in ("cancelled", "terminated") and s.total_amount
            )
            if len(self) == len(total_paid):
                phrase = _(
                    "Attached you will find a payment slip to set up a standing order "
                    "for monthly payment of the sponsorship"
                )
            else:
                phrase = _(
                    "Attached you will find the payment slip that will allow you "
                    "to increase your current standing order to CHF %s.-"
                ) % int(sum(total_paid.mapped("total_amount")))
        elif "LSV" in payment_mode or "Postfinance" in payment_mode:
            if "mandate" in self.mapped("state"):
                phrase = _(
                    "Attached you will find the LSV or Direct Debit authorization "
                    "form to fill in if you haven't already done it!"
                )
            else:
                phrase = _(
                    "We will continue to withdraw the amount for "
                    "the sponsorship from your account."
                )
        else:
            freq = self.mapped("group_id.recurring_value")[:1]
            if freq == 12:
                phrase = _(
                    "Attached you will find a payment slip for the annual "
                    "sponsorship payment"
                )
            else:
                phrase = _(
                    "Attached you will find the payment slips for the "
                    "sponsorship payment"
                )
        return phrase

    def _compute_birthday_paid(self):
        today = datetime.today()
        in_three_months = today + relativedelta(months=3)
        since_six_months = today - relativedelta(months=6)
        for sponsorship in self:
            sponsorship.birthday_paid = self.env["sponsorship.gift"].search(
                [
                    ("sponsorship_id", "=", sponsorship.id),
                    ("gift_date", ">=", since_six_months),
                    ("gift_date", "<", in_three_months),
                    ("sponsorship_gift_type", "=", "Birthday"),
                ]
            )

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.model
    def send_daily_communication(self):
        """
        Prepare daily communications to send.
        - Birthday reminders
        """
        logger.info("Sponsorship Planned Communications started!")

        logger.info("....Creating Birthday Reminder Communications")
        self._send_reminders_for_birthday_in_1day_or_2months()

        logger.info("Sponsorship Planned Communications finished!")

    @api.model
    def _send_reminders_for_birthday_in_1day_or_2months(self):
        module = "partner_communication_switzerland."
        logger.info("....Creating Birthday Reminder Communications")
        today = datetime.now()

        in_two_month = today + relativedelta(months=2)
        sponsorships_with_birthday_in_two_months = (
            self._get_sponsorships_with_child_birthday_on(in_two_month)
        )
        self._send_birthday_reminders(
            sponsorships_with_birthday_in_two_months,
            self.env.ref(module + "planned_birthday_reminder"),
        )

        tomorrow = today + relativedelta(days=1)
        sponsorships_with_birthday_tomorrow = (
            self._get_sponsorships_with_child_birthday_on(tomorrow)
        )

        sponsorships_to_avoid = sponsorships_with_birthday_tomorrow.filtered(
            lambda s: s.type == "SWP"
        )

        for sponsorship in sponsorships_with_birthday_tomorrow:
            sponsorship_correspondences = self.env["correspondence"].search_count(
                [
                    ("sponsorship_id", "=", sponsorship.id),
                    ("direction", "=", "Supporter To Beneficiary"),
                    (
                        "scanned_date",
                        ">=",
                        fields.Date.to_string(datetime.now() - relativedelta(months=2)),
                    ),
                ]
            )

            if sponsorship_correspondences:
                sponsorships_to_avoid += sponsorship
                continue

            sponsorship_gifts = self.env["sponsorship.gift"].search(
                [
                    ("sponsorship_id", "=", sponsorship.id),
                    (
                        "gift_date",
                        ">=",
                        fields.Date.to_string(datetime.now() - relativedelta(months=2)),
                    ),
                    ("sponsorship_gift_type", "=", "Birthday"),
                ]
            )

            if sponsorship_gifts:
                sponsorships_to_avoid += sponsorship

        self._send_birthday_reminders(
            sponsorships_with_birthday_tomorrow - sponsorships_to_avoid,
            self.env.ref(module + "birthday_remainder_1day_before"),
        )

    @api.model
    def _send_birthday_reminders(self, sponsorships, communication):
        communication_jobs = self.env["partner.communication.job"]
        for sponsorship in sponsorships:
            send_to_payer = (
                sponsorship.send_gifts_to == "partner_id"
                and sponsorship.partner_id.birthday_reminder
            )
            send_to_correspondent = sponsorship.correspondent_id.birthday_reminder
            try:
                communication_jobs += sponsorship.send_communication(
                    communication,
                    correspondent=send_to_correspondent,
                    both=send_to_payer and send_to_correspondent,
                )
            except Exception:
                # In any case, we don't want to stop email generation!
                logger.error("Error during birthday reminder: ", exc_info=True)

    @api.model
    def _get_sponsorships_with_child_birthday_on(self, birth_day):
        corresp_compass_tag = "partner_compassion.res_partner_category_corresp_compass"
        return self.search(
            [
                ("child_id.birthdate", "like", birth_day.strftime("%%-%m-%d")),
                "|",
                ("correspondent_id.birthday_reminder", "=", True),
                ("partner_id.birthday_reminder", "=", True),
                "|",
                "|",
                ("correspondent_id.email", "!=", False),
                ("partner_id.email", "!=", False),
                "&",
                ("type", "=", "SWP"),
                ("correspondent_id.mobile", "!=", False),
                ("state", "=", "active"),
                ("type", "like", "S"),
                ("partner_id.ref", "!=", "1502623"),
                # (above) if partner is not Demaurex
                (
                    "partner_id.category_id",
                    "not in",
                    self.env.ref(corresp_compass_tag).ids,
                ),
            ]
        ).filtered(
            lambda c: not (
                c.child_id.project_id.lifecycle_ids
                and c.child_id.project_id.hold_s2b_letters
            )
        )

    def get_bvr_gift_attachment(self, products, background=False):
        """
        Get a BVR communication attachment for given gift products.
        :param products: product.product recordset
        :param background: wheter to print background or not
        :return: dict {attachment_name: [report_name, pdf_data]}
        """
        report = "report_compassion.bvr_gift_sponsorship"
        attachments = dict()
        partner_lang = self.mapped("correspondent_id")[0].lang
        product_name = products[0].with_context(lang=partner_lang).name
        report_ref = self.env.ref("report_compassion.report_bvr_gift_sponsorship")
        pdf_data = report_ref._render_qweb_pdf(
            self.ids,
            data={
                "doc_ids": self.ids,
                "product_ids": products.ids,
                "background": background,
            },
        )[0]
        attachments[product_name + ".pdf"] = [
            report,
            base64.encodebytes(pdf_data),
        ]
        return attachments

    def intersect(self, other):
        """Utility to intersect from template"""
        return self & other

    def must_pay_next_year(self):
        """Utility to tell if sponsorship must be paid next year."""
        return max(self.mapped("months_paid")) < 24

    def action_sub_reject(self):
        res = super().action_sub_reject()
        no_sub_config = self.env.ref("partner_communication_switzerland.planned_no_sub")
        communications = self.with_context({}).send_communication(
            no_sub_config, both=True
        )
        if res:
            res = {
                "name": communications[0].subject,
                "type": "ir.actions.act_window",
                "view_type": "form",
                "view_mode": "tree,form",
                "res_model": "partner.communication.job",
                "domain": [("id", "in", communications.ids)],
                "target": "current",
                "context": self.env.context,
            }
        return res

    ##########################################################################
    #                            WORKFLOW METHODS                            #
    ##########################################################################
    def contract_waiting_mandate(self):
        res = super().contract_waiting_mandate()
        new_spons = self.filtered(
            lambda c: c.type in SPONSORSHIP_TYPE_LIST + ["CSP"] and not c.is_active
        )
        new_spons._new_dossier()
        csp = self.filtered(
            lambda s: "6014"
            in s.mapped("contract_line_ids.product_id.property_account_income_id.code")
        )
        if csp:
            module = "partner_communication_switzerland."
            other_csp_config = self.env.ref(module + "csp_mail")
            (
                csp.filtered(lambda s: s.type != "CSP")
                .with_context({})
                .send_communication(other_csp_config, correspondent=False)
            )

        return res

    def notify_sds_new_sponsorship(self):
        self.ensure_one()
        config_settings = self.env["res.config.settings"].sudo()
        sds_partner_id = config_settings.get_sponsorship_de_id()
        if self.correspondent_id.lang == "fr_CH":
            sds_partner_id = config_settings.get_sponsorship_fr_id()
        if self.correspondent_id.lang == "it_IT":
            sds_partner_id = config_settings.get_sponsorship_it_id()
        sds_user = (
            self.env["res.users"]
            .sudo()
            .search([("partner_id", "=", int(sds_partner_id))])
        )

        if sds_user.id:
            self.correspondent_id.activity_schedule(
                "partner_communication_switzerland.activity_check_partner_no_communication",
                date_deadline=datetime.date(datetime.today() + timedelta(weeks=1)),
                summary=_("Notify partner of new sponsorship"),
                note=_(
                    "A sponsorship was added to a partner with the communication "
                    'settings set to "don\'t inform", please notify him of it'
                ),
                user_id=sds_user.id,
            )

    def contract_waiting(self):
        mandates_valid = self.filtered(lambda c: c.state == "mandate")
        res = super().contract_waiting()

        for contract in self:
            old_sponsorships = contract.correspondent_id.sponsorship_ids.filtered(
                lambda c, ref=contract: c.state != "cancelled"
                and c.start_date
                and c.start_date < ref.start_date
            )
            contract.is_first_sponsorship = not old_sponsorships

            # Notify SDS when partner has "don't inform" as comm setting
            if (
                contract.correspondent_id.global_communication_delivery_preference
                == "none"
            ):
                # Notify the same SDS partner as the one notified when a sponsorship
                # is created from the website so that we can manage partner language
                self.notify_sds_new_sponsorship()

        self.filtered(
            lambda c: c.type in SPONSORSHIP_TYPE_LIST + ["CSP"]
            and not c.is_active
            and c not in mandates_valid
        ).with_context({})._new_dossier()

        csp = self.filtered(
            lambda s: "6014"
            in s.mapped("contract_line_ids.product_id.property_account_income_id.code")
        )
        if csp:
            module = "partner_communication_switzerland."
            other_csp_config = self.env.ref(module + "csp_mail")
            (
                csp.filtered(lambda s: s.type != "CSP")
                .with_context({})
                .send_communication(other_csp_config, correspondent=False)
            )

        return res

    def contract_active(self):
        """Remove waiting reminders if any"""
        self.env["partner.communication.job"].search(
            [
                ("config_id.name", "ilike", "Waiting reminder"),
                ("state", "!=", "done"),
                ("partner_id", "in", self.mapped("partner_id").ids),
            ]
        ).unlink()
        # Send sponsorship confirmation for write&pray sponsorships
        # that didn't get through waiting state (would already have the communication)
        wp = self.filtered(lambda s: s.type in ["SC", "SWP"] and s.state == "draft")
        super().contract_active()
        wp._new_dossier()
        return True

    def _contract_terminated(self, vals):
        vals["new_picture"] = False
        return super()._contract_terminated(vals)

    def cancel_sub_validation(self):
        return self.write({"sub_proposal_date": False})

    @api.model
    def send_wrpr_letter_reminder(self):
        wrprs = self.search(
            [
                ("type", "=", "SWP"),
                ("state", "=", "active"),
                ("correspondent_id.mobile", "!=", False),
                ("correspondent_id.lang", "not in", ["it_IT", "en_US"]),
            ]
        )
        letter_reminder = self.env.ref(
            "partner_communication_switzerland.sponsorship_wrpr_reminder"
        )
        comms = self.env["partner.communication.job"]
        for wrpr in wrprs:
            start_days = (fields.Datetime.now() - wrpr.start_date).days
            if wrpr.last_letter > 545 or (
                not wrpr.sponsor_letter_ids and start_days > 545
            ):
                comms += wrpr.send_communication(letter_reminder)
        comms.send()
        return True

    @api.model
    def send_wrpr_contribution_reminder(self):
        wrprs = self.search(
            [
                ("type", "=", "SWP"),
                ("state", "=", "active"),
                ("correspondent_id.mobile", "!=", False),
                ("correspondent_id.lang", "not in", ["it_IT", "en_US"]),
                ("total_amount", ">", 0),
                ("invoice_line_ids.payment_state", "!=", "paid"),
            ]
        )
        contribution_reminder = self.env.ref(
            "partner_communication_switzerland.wrpr_contribution_reminder_config"
        )
        comms = self.env["partner.communication.job"]
        first_reminder = comms
        sub_reminders = comms
        one_month_ago = fields.Date.today() - relativedelta(months=1)
        for wrpr in wrprs.filtered(
            lambda w: not w.last_paid_invoice_date
            and w.invoice_line_ids[:1].due_date < one_month_ago
        ):
            already_reminded = comms.search_count(
                [
                    ("config_id", "=", contribution_reminder.id),
                    ("partner_id", "=", wrpr.partner_id.id),
                    ("object_ids", "like", wrpr.id),
                    ("state", "=", "done"),
                ]
            )
            job = wrpr.send_communication(contribution_reminder, correspondent=False)
            if already_reminded:
                sub_reminders += job
            else:
                first_reminder += job
        sub_reminders.write({"send_mode": "physical"})
        # first_reminder.send()  (not sure if we want to send it automatically)
        return True

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _new_dossier(self):
        """
        Sends the dossier of the new sponsorship to both payer and
        correspondent.
        """
        for spo in self:
            if spo.correspondent_id.id != spo.partner_id.id:
                corresp = spo.correspondent_id
                payer = spo.partner_id
                if corresp.contact_address != payer.contact_address:
                    spo._send_new_dossier()
                    spo._send_new_dossier(correspondent=False)
                    continue
            spo._send_new_dossier()

    def _send_new_dossier(self, correspondent=True):
        """
        Sends the New Dossier communications if it wasn't already sent for
        this sponsorship.
        :param correspondent: True if communication is sent to correspondent
        :return: None
        """
        self.ensure_one()
        swiss = "partner_communication_switzerland."
        common = "partner_communication_compassion."
        new_dossier = self.env.ref(swiss + "config_onboarding_sponsorship_confirmation")
        print_dossier = self.env.ref(common + "planned_dossier")
        wrpr_welcome = self.env.ref(swiss + "config_wrpr_welcome")
        transfer = self.env.ref(common + "new_dossier_transfer")
        child_picture = self.env.ref(swiss + "config_onboarding_photo_by_post")
        survival_config = self.env.ref(swiss + "csp_1") + self.env.ref(swiss + "csp_2a")
        partner = self.correspondent_id if correspondent else self.partner_id
        if self.parent_id.sds_state == "sub":
            # No automated communication in this case. The staff can manually send
            # the SUB Accept communication when appropriate
            return True
        elif self.origin_id.type == "transfer":
            configs = transfer
        elif (
            not partner.email
            or partner.global_communication_delivery_preference == "physical"
        ):
            configs = print_dossier
        elif self.type == "SWP":
            configs = wrpr_welcome + child_picture
        elif self.type == "CSP":
            configs = survival_config
        else:
            configs = new_dossier + child_picture
        for config in configs:
            already_sent = self.env["partner.communication.job"].search(
                [
                    ("partner_id", "=", partner.id),
                    ("config_id", "=", config.id),
                    ("object_ids", "like", str(self.id)),
                    ("state", "=", "done"),
                ]
            )
            if not already_sent:
                comms = self.with_context({}).send_communication(config, correspondent)
                if config == wrpr_welcome:
                    comms.write({"send_mode": "sms"})
        return True

    def _can_activate_contract(self, contract: "RecurringContract"):
        """Activate sub proposal contract if it is waiting for payment and
        at least two invoices have been paid."""
        if contract.sub_proposal_date:
            sub_proposal_date = contract.sub_proposal_date.replace(day=1)
            paid_invoices = self.env["account.move"].search(
                [
                    ("invoice_date_due", ">=", sub_proposal_date),
                    ("payment_state", "=", "paid"),
                    ("partner_id", "=", contract.partner_id.id),
                    ("line_ids.contract_id", "=", contract.id),
                ]
            )

            return len(paid_invoices) >= 2

        return super()._can_activate_contract(contract)
