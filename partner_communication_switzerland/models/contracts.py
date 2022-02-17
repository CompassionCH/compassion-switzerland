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
from datetime import datetime, date, timedelta

from dateutil.relativedelta import relativedelta

from odoo import api, models, fields, _

logger = logging.getLogger(__name__)


class RecurringContract(models.Model):
    """
    Add method to send all planned communication of sponsorships.
    """

    _inherit = ["recurring.contract", "translatable.model"]
    _name = "recurring.contract"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    order_photo = fields.Boolean(
        help="Indicates that the child has a new picture to be ordered with "
             "Smartphoto."
    )
    birthday_paid = fields.Many2many(
        "sponsorship.gift", compute="_compute_birthday_paid", readonly=False
    )
    due_invoice_ids = fields.Many2many(
        "account.invoice", compute="_compute_due_invoices",
        store=True, readonly=False
    )
    period_paid = fields.Boolean(
        compute="_compute_period_paid",
        help="Tells if the advance billing period is already paid",
    )
    months_due = fields.Integer(compute="_compute_due_invoices", store=True)
    send_introduction_letter = fields.Boolean(
        string="Send B2S intro letter to sponsor", default=True
    )
    origin_type = fields.Selection(related="origin_id.type")
    origin_name = fields.Char(related="origin_id.name")
    is_first_sponsorship = fields.Boolean(readonly=True)

    onboarding_start_date = fields.Date(help="Indicates when the first email of "
                                             "the onboarding process was sent.",
                                        copy=False)
    sub_proposal_date = fields.Date(help="Trigger for automatic SUB sponsorship validation after 2 weeks")

    @api.onchange("type")
    def _create_empty_lines_for_correspondence(self):
        super()._create_empty_lines_for_correspondence()
        if self.type == "SWP" and not self.correspondent_id.mobile:
            return {
                "warning": {
                    "title": "Write&Pray",
                    "message": "The correspondent doesn't have a mobile phone set. "
                               "Please check this otherwise he or she won't receive "
                               "the communications by SMS."
                }
            }
        if self.type == "SWP" and not self.correspondent_id.is_young:
            return {
                "warning": {
                    "title": "Write&Pray",
                    "message": "The correspondent is not a young person. "
                               "Please check that this sponsorship is indeed a "
                               "Write&Pray, or use the 'Correspondence' type otherwise."
                }
            }

    @api.onchange("origin_id")
    def _do_not_send_letter_to_transfer(self):
        if self.origin_id.type == "transfer" or self.origin_id.name == "Reinstatement":
            self.send_introduction_letter = False
        # If origin is switched back from a transer,
        # field should be reset to default
        else:
            self.send_introduction_letter = True

    @api.multi
    def _on_change_correspondant(self, correspondent_id):
        # Don't send introduction letter when correspondent is changed
        cancelled_sponsorships = super()._on_change_correspondant(correspondent_id)
        cancelled_sponsorships.write({"send_introduction_letter": False})
        return cancelled_sponsorships

    def get_payment_type_attachment_string(self):
        payment_mode = self.with_context(lang="en_US").mapped(
            "payment_mode_id")[:1].name
        if payment_mode == "Permanent Order":
            total_paid = self.mapped("group_id.contract_ids").filtered(
                lambda s: s.state not in ("cancelled", "terminated") and s.total_amount)
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
                phrase = _("Attached you will find a payment slip for the annual "
                           "sponsorship payment")
            else:
                phrase = _("Attached you will find the payment slips for the "
                           "sponsorship payment")
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

    @api.depends("invoice_line_ids", "invoice_line_ids.state")
    def _compute_due_invoices(self):
        """
        Useful for reminders giving open invoices in the past.
        """
        this_month = date.today().replace(day=1)
        for contract in self:
            if (
                    contract.child_id.project_id.suspension != "fund-suspended"
                    and contract.type not in ["SC", "SWP"]
            ):
                invoice_lines = contract.invoice_line_ids.with_context(
                    lang="en_US"
                ).filtered(
                    lambda i: i.state == "open"
                    and i.due_date < this_month
                    and i.invoice_id.invoice_category == "sponsorship"
                )
                contract.due_invoice_ids = invoice_lines.mapped("invoice_id")
                contract.amount_due = \
                    int(sum(invoice_lines.mapped("price_subtotal")))
                months = set()
                for invoice in invoice_lines.mapped("invoice_id"):
                    idate = invoice.date
                    months.add((idate.month, idate.year))
                contract.months_due = len(months)
            else:
                contract.months_due = 0

    @api.multi
    def _compute_period_paid(self):
        for contract in self:
            advance_billing = contract.group_id.advance_billing_months
            this_month = date.today().month
            # Don't consider next year in the period to pay
            to_pay_period = min(this_month + advance_billing, 12)
            # Exception for december, we will consider next year
            if this_month == 12:
                to_pay_period += advance_billing
            contract.period_paid = contract.months_paid >= to_pay_period

    @api.multi
    def compute_due_invoices(self):
        self._compute_due_invoices()
        return True

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def send_communication(self, communication,
                           correspondent=True, both=False):
        """
        Sends a communication to selected sponsorships.
        :param communication: the communication config to use
        :param correspondent: put to false for sending to payer instead of
                              correspondent.
        :param both:          send to both correspondent and payer
                              (overrides the previous parameter)
        :return: communication created recordset
        """
        partner_field = "correspondent_id" if correspondent else "partner_id"
        partners = self.mapped(partner_field)
        communications = self.env["partner.communication.job"]
        if both:
            for contract in self:
                communications += self.env["partner.communication.job"].create(
                    {
                        "config_id": communication.id,
                        "partner_id": contract.partner_id.id,
                        "object_ids": self.env.context.get(
                            "default_object_ids", contract.id
                        ),
                        "user_id": communication.user_id.id,
                    }
                )
                if contract.correspondent_id != contract.partner_id:
                    communications += \
                        self.env["partner.communication.job"].create({
                            "config_id": communication.id,
                            "partner_id": contract.correspondent_id.id,
                            "object_ids": self.env.context.get(
                                "default_object_ids", contract.id
                            ),
                            "user_id": communication.user_id.id,
                            }
                        )
        else:
            for partner in partners:
                objects = self.filtered(
                    lambda c: c.correspondent_id == partner
                    if correspondent
                    else c.partner_id == partner
                )
                communications += self.env["partner.communication.job"].create(
                    {
                        "config_id": communication.id,
                        "partner_id": partner.id,
                        "object_ids": self.env.context.get(
                            "default_object_ids", objects.ids
                        ),
                        "user_id": communication.user_id.id,
                    }
                )
        return communications

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
        sponsorships_with_birthday_in_two_months = \
            self._get_sponsorships_with_child_birthday_on(in_two_month)
        self._send_birthday_reminders(
            sponsorships_with_birthday_in_two_months,
            self.env.ref(module + "planned_birthday_reminder"),
        )

        tomorrow = today + relativedelta(days=1)
        sponsorships_with_birthday_tomorrow = \
            self._get_sponsorships_with_child_birthday_on(tomorrow)

        sponsorships_to_avoid = self.env["recurring.contract"]

        for sponsorship in sponsorships_with_birthday_tomorrow:
            sponsorship_correspondences = \
                self.env["correspondence"].search_count(
                    [
                        ("sponsorship_id", "=", sponsorship.id),
                        ("direction", "=", "Supporter To Beneficiary"),
                        (
                            "scanned_date",
                            ">=",
                            fields.Date.to_string(
                                datetime.now() - relativedelta(months=2)),
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
                        fields.Date.to_string(
                            datetime.now() - relativedelta(months=2)),
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
                sponsorship.send_gifts_to == "partner_id" and sponsorship.partner_id.birthday_reminder
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
        corresp_compass_tag = \
            "partner_compassion.res_partner_category_corresp_compass"
        return self.search(
            [
                ("child_id.birthdate", "like", birth_day.strftime("%%-%m-%d")),
                "|",
                ("correspondent_id.birthday_reminder", "=", True),
                ("partner_id.birthday_reminder", "=", True),
                "|",
                ("correspondent_id.email", "!=", False),
                ("partner_id.email", "!=", False),
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

    @api.model
    def send_sponsorship_reminders(self):
        logger.info("Creating Sponsorship Reminders")
        today = datetime.now()
        first_day_of_month = date(today.year, today.month, 1)
        first_reminder_config = self.env.ref(
            "partner_communication_switzerland.sponsorship_reminder_1"
        )
        second_reminder_config = self.env.ref(
            "partner_communication_switzerland.sponsorship_reminder_2"
        )
        first_reminder = self.with_context(
            default_print_subject=False,
            default_auto_send=False,
            default_print_header=True,
        )
        second_reminder = self.with_context(
            default_print_subject=False,
            default_auto_send=False,
            default_print_header=True,
        )
        twenty_ago = today - relativedelta(days=20)
        comm_obj = self.env["partner.communication.job"]
        search_domain = [
            ("state", "in", ("active", "mandate")),
            ("global_id", "!=", False),
            ("type", "like", "S"),
            "|",
            ("child_id.project_id.suspension", "!=", "fund-suspended"),
            ("child_id.project_id.suspension", "=", False),
        ]

        for sponsorship in self.search(
                search_domain + [("months_due", ">", 1)]):
            reminder_search = [
                (
                    "config_id",
                    "in",
                    [first_reminder_config.id, second_reminder_config.id],
                ),
                ("state", "=", "done"),
                ("object_ids", "like", str(sponsorship.id)),
            ]
            # Look if first reminder was sent previous month (send second
            # reminder in that case)
            # avoid taking into account reminder that the partner already took care of
            # we substract month due to the first of the month to get the older threshold
            # this also prevent reminder_1 to be sent after an already sent reminder_2
            older_threshold = first_day_of_month - relativedelta(months=sponsorship.months_due)

            has_first_reminder = comm_obj.search_count(
                reminder_search
                + [("sent_date", ">=", older_threshold),
                   ("sent_date", "<", twenty_ago)]
            )
            if has_first_reminder:
                second_reminder += sponsorship
            else:
                # Send first reminder only if one was not already sent less
                # than twenty days ago
                has_first_reminder = comm_obj.search_count(
                    reminder_search + [("sent_date", ">=", twenty_ago)]
                )
                if not has_first_reminder:
                    first_reminder += sponsorship
        first_reminder.send_communication(
            first_reminder_config, correspondent=False)
        second_reminder.send_communication(
            second_reminder_config, correspondent=False)
        logger.info("Sponsorship Reminders created!")
        return True

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
        report_ref = self.env.ref(
            "report_compassion.report_bvr_gift_sponsorship")
        pdf_data = report_ref.render_qweb_pdf(
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
        """ Utility to intersect from template """
        return self & other

    def must_pay_next_year(self):
        """ Utility to tell if sponsorship must be paid next year. """
        return max(self.mapped("months_paid")) < 24

    @api.multi
    def action_sub_reject(self):
        res = super().action_sub_reject()
        no_sub_config = self.env.ref("partner_communication_switzerland.planned_no_sub")
        self.with_context({}).send_communication(no_sub_config, both=True)
        return res

    ##########################################################################
    #                            WORKFLOW METHODS                            #
    ##########################################################################
    @api.multi
    def contract_waiting_mandate(self):
        res = super().contract_waiting_mandate()
        new_spons = self.filtered(lambda c: "S" in c.type and not c.is_active)
        new_spons._new_dossier()
        csp = self.filtered(
            lambda s: "6014" in s.mapped(
                "contract_line_ids.product_id.property_account_income_id.code")
        )
        if csp:
            module = "partner_communication_switzerland."
            selected_config = self.env.ref(module + "csp_mail")
            csp.with_context({}).send_communication(
                selected_config, correspondent=False)

        return res

    def notify_sds_new_sponsorship(self):
        self.ensure_one()
        config_settings = self.env["res.config.settings"].sudo()
        sds_partner_id = config_settings.get_sponsorship_de_id()
        if self.correspondent_id.lang == 'fr_CH':
            sds_partner_id = config_settings.get_sponsorship_fr_id()
        if self.correspondent_id.lang == 'it_IT':
            sds_partner_id = config_settings.get_sponsorship_it_id()
        sds_user = self.env['res.users'].sudo().search([('partner_id', '=', int(sds_partner_id))])

        if sds_user.id:
            self.correspondent_id.activity_schedule(
                'partner_communication_switzerland.activity_check_partner_no_communication',
                date_deadline=datetime.date(datetime.today() + timedelta(weeks=1)),
                summary=_("Notify partner of new sponsorship"),
                note=_("A sponsorship was added to a partner with the communication settings set to \"don't " +
                       "inform\", please notify him of it"),
                user_id=sds_user.id
            )
    @api.multi
    def contract_waiting(self):
        mandates_valid = self.filtered(lambda c: c.state == "mandate")
        res = super().contract_waiting()

        for contract in self:
            old_sponsorships = contract.correspondent_id.sponsorship_ids.filtered(
                lambda c: c.state != "cancelled" and c.start_date
                and c.start_date < contract.start_date)
            contract.is_first_sponsorship = not old_sponsorships

            # Notify SDS when partner has "don't inform" as comm setting
            if contract.correspondent_id.global_communication_delivery_preference == "none":
                # Notify the same SDS partner as the one notified when a sponsorship is created from the website
                # so that we can manage partner language
                self.notify_sds_new_sponsorship()

        self.filtered(
            lambda c: "S" in c.type
                      and not c.is_active
                      and c not in mandates_valid
        ).with_context({})._new_dossier()

        csp = self.filtered(
            lambda s: "6014" in s.mapped(
                "contract_line_ids.product_id.property_account_income_id.code")
        )
        if csp:
            module = "partner_communication_switzerland."
            selected_config = self.env.ref(module + "csp_mail")
            csp.with_context({}).send_communication(
                selected_config, correspondent=False)

        return res

    @api.multi
    def contract_active(self):
        """ Remove waiting reminders if any """
        self.env["partner.communication.job"].search(
            [
                ("config_id.name", "ilike", "Waiting reminder"),
                ("state", "!=", "done"),
                ("partner_id", "in", self.mapped("partner_id").ids),
            ]
        ).unlink()
        # Send sponsorship confirmation for write&pray sponsorships
        # that didn't get through waiting state (would already have the communication)
        wp = self.filtered(
            lambda s: s.type in ["SC", "SWP"] and s.state == "draft"
        )
        super().contract_active()
        wp._new_dossier()
        return True

    @api.multi
    def contract_terminated(self):
        super().contract_terminated()
        if self.child_id:
            self.child_id.sponsorship_ids[0].order_photo = False
        return True

    @api.multi
    def contract_cancelled(self):
        # Remove pending communications
        for contract in self:
            self.env["partner.communication.job"].search([
                ("config_id.model_id.model", "=", self._name),
                "|", ("partner_id", "=", contract.partner_id.id),
                ("partner_id", "=", contract.correspondent_id.id),
                ("object_ids", "like", contract.id),
                ("state", "=", "pending")
            ]).unlink()
        super().contract_cancelled()
        return True

    @api.multi
    def action_cancel_draft(self):
        """ Cancel communication"""
        super().action_cancel_draft()
        cancel_config = self.env.ref(
            "partner_communication_switzerland.sponsorship_cancellation")
        for contract in self:
            self.env["partner.communication.job"].search([
                ("config_id", "=", cancel_config.id),
                "|", ("partner_id", "=", contract.partner_id.id),
                ("partner_id", "=", contract.correspondent_id.id),
                ("object_ids", "like", contract.id),
                ("state", "=", "pending")
            ]).unlink()
        return True

    def cancel_sub_validation(self):
        return self.write({"sub_proposal_date": False})

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    @api.multi
    def _on_sponsorship_finished(self):
        super()._on_sponsorship_finished()
        cancellation = self.env.ref(
            "partner_communication_switzerland.sponsorship_cancellation"
        )
        no_sub = self.env.ref("partner_communication_switzerland.planned_no_sub")
        depart = self.env.ref("sponsorship_compassion.end_reason_depart")

        # prevent normal communication on unexpected hold end. in this particular case
        # a special communication will be send.
        s_to_notify = self.filtered(lambda s: not s._is_unexpected_end())

        # Send cancellation for regular sponsorships
        s_to_notify.filtered(
            lambda s: s.end_reason_id != depart and not s.parent_id
        ).with_context({}).send_communication(cancellation, both=True)
        # Send NO SUB letter if activation is less than two weeks ago
        # otherwise send Cancellation letter for SUB sponsorships
        activation_limit = date.today() - relativedelta(days=15)
        s_to_notify.filtered(
            lambda s: s.end_reason_id != depart
            and s.parent_id
            and (
                s.activation_date
                and fields.Date.from_string(s.activation_date) < activation_limit
            )
        ).with_context({}).send_communication(cancellation, both=True)
        s_to_notify.filtered(
            lambda s: s.end_reason_id != depart
            and s.parent_id
            and (
                not s.activation_date
                or fields.Date.from_string(s.activation_date) >= activation_limit
            )
        ).with_context({}).send_communication(no_sub, both=True)

    def _is_unexpected_end(self):
        """Check if sponsorship hold had an unexpected end or not."""
        self.ensure_one()

        # subreject could happened before hold expiration and should not be considered
        # as unexpected
        subreject = self.env.ref("sponsorship_compassion.end_reason_subreject")

        if self.end_reason_id == subreject:
            return False

        return self.hold_id and not datetime.now() > self.hold_id.expiration_date

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
        module = "partner_communication_switzerland."
        new_dossier = self.env.ref(
            module + "config_onboarding_sponsorship_confirmation")
        print_dossier = self.env.ref(module + "planned_dossier")
        wrpr_welcome = self.env.ref(module + "config_wrpr_welcome")
        transfer = self.env.ref(module + "new_dossier_transfer")
        child_picture = self.env.ref(module + "config_onboarding_photo_by_post")
        partner = self.correspondent_id if correspondent else self.partner_id
        if self.parent_id.sds_state == "sub":
            # No automated communication in this case. The staff can manually send
            # the SUB Accept communication when appropriate
            return True
        elif self.origin_id.type == "transfer":
            configs = transfer
        elif not partner.email or \
                partner.global_communication_delivery_preference == "physical":
            configs = print_dossier
        elif self.type == "SWP":
            configs = wrpr_welcome + child_picture
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
