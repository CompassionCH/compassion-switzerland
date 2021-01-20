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
from datetime import datetime, date

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
    payment_type_attachment = fields.Char(
        compute="_compute_payment_type_attachment")
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

    def _compute_payment_type_attachment(self):
        for contract in self:
            payment_mode = (
                contract.with_context(lang="en_US").payment_mode_id.name or ""
            )
            if payment_mode == "Permanent Order":
                phrase = _(
                    "1 payment slip to set up a standing order ("
                    "monthly payment of the sponsorship)"
                )
            elif "LSV" in payment_mode or "Postfinance" in payment_mode:
                if contract.state == "mandate":
                    phrase = _(
                        "1 LSV or Direct Debit authorization form to "
                        "fill in if you don't already have done it!"
                    )
                else:
                    phrase = _(
                        "We will continue to withdraw the amount for "
                        "the sponsorship from your account."
                    )
            else:
                freq = contract.group_id.recurring_value
                if freq == 12:
                    phrase = _("1 payment slip for the annual sponsorship "
                               "payment")
                else:
                    phrase = _("payment slips for the sponsorship payment")
            contract.payment_type_attachment = phrase

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
                    and contract.type != "SC"
            ):
                invoice_lines = contract.invoice_line_ids.with_context(
                    lang="en_US"
                ).filtered(
                    lambda i: i.state == "open"
                    and i.due_date < this_month
                    and i.invoice_id.invoice_type == "sponsorship"
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

        # logger.info("....Send Welcome Activations Letters")
        # self._send_welcome_active_letters_for_activated_sponsorships()

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
            send_to_partner_as_he_paid_the_gift = (
                sponsorship.send_gifts_to == "partner_id"
            )
            try:
                communication_jobs += sponsorship.send_communication(
                    communication,
                    correspondent=True,
                    both=send_to_partner_as_he_paid_the_gift,
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
        ninety_ago = today - relativedelta(days=90)
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
        # Recompute due invoices of multi-months payers, because
        # due months are only recomputed when new invoices are generated
        # which could take up to one year for yearly payers.
        multi_month = self.search(
            search_domain + [("group_id.advance_billing_months", ">", 3)]
        )
        multi_month.compute_due_invoices()
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
            has_first_reminder = comm_obj.search_count(
                reminder_search
                + [("sent_date", ">=", ninety_ago),
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
        no_sub_config = self.env.ref(
            "partner_communication_switzerland.planned_no_sub")
        self.with_context({}).send_communication(
            no_sub_config, correspondent=False)
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

    @api.multi
    def contract_waiting(self):
        mandates_valid = self.filtered(lambda c: c.state == "mandate")
        res = super().contract_waiting()
        self.filtered(
            lambda c: "S" in c.type
                      and not c.is_active
                      and c not in mandates_valid
        ).with_context({})._new_dossier()

        csp_product = self.env.ref(
            "sponsorship_switzerland.product_template_fund_csp")
        csp = self.filtered(
            lambda s: csp_product in s.contract_line_ids.mapped(
                "product_id.product_tmpl_id"))
        if csp:
            module = "partner_communication_switzerland."
            selected_config = self.env.ref(module + "csp_mail")
            csp.with_context({}).send_communication(
                selected_config, correspondent=False)

        for contract in self:
            old_sponsorships = contract.correspondent_id.sponsorship_ids.filtered(
                lambda c: c.state != "cancelled" and c.start_date
                and c.start_date < contract.start_date)
            contract.is_first_sponsorship = not old_sponsorships
            if not old_sponsorships:
                # Invite partner for next zoom
                zoom_session = self.env["res.partner.zoom.session"].with_context(
                    lang=contract.correspondent_id.lang).get_next_session()
                if zoom_session:
                    zoom_session.add_participant(contract.correspondent_id)

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
        # Send new dossier for write&pray sponsorships
        # that didn't get through waiting state (would already have the communication)
        self.filtered(
            lambda s: s.type == "SC" and s.state == "draft"
        ).with_context({}).send_communication(
            self.env.ref(
                "partner_communication_switzerland.sponsorship_dossier_wrpr"
            )
        )
        return super().contract_active()

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
        # Send cancellation for regular sponsorships
        self.filtered(
            lambda s: s.end_reason_id != depart and not s.parent_id
        ).with_context({}).send_communication(cancellation, both=True)
        # Send NO SUB letter if activation is less than two weeks ago
        # otherwise send Cancellation letter for SUB sponsorships
        activation_limit = date.today() - relativedelta(days=15)
        self.filtered(
            lambda s: s.end_reason_id != depart
            and s.parent_id
            and (
                s.activation_date
                and fields.Date.from_string(s.activation_date) < activation_limit
            )
        ).with_context({}).send_communication(cancellation, correspondent=False)
        self.filtered(
            lambda s: s.end_reason_id != depart
            and s.parent_id
            and (
                not s.activation_date
                or fields.Date.from_string(s.activation_date) >= activation_limit
            )
        ).with_context({}).send_communication(no_sub, correspondent=False)

    def _new_dossier(self):
        """
        Sends the dossier of the new sponsorship to both payer and
        correspondent.
        """
        module = "partner_communication_switzerland."
        new_dossier = self.env.ref(module + "config_onboarding_step1")
        child_picture = self.env.ref(module + "config_onboarding_photo_by_post")

        for spo in self:
            spo.send_communication(child_picture)
            if spo.correspondent_id.id != spo.partner_id.id:
                corresp = spo.correspondent_id
                payer = spo.partner_id
                if corresp.contact_address != payer.contact_address:
                    spo._send_new_dossier(new_dossier)
                    spo._send_new_dossier(new_dossier, correspondent=False)
                    continue
            spo._send_new_dossier(new_dossier)

    def _send_new_dossier(self, communication_config, correspondent=True):
        """
        Sends the New Dossier if it wasn't already sent for this sponsorship.
        :param communication_config: Communication Config record to search.
        :param correspondent: True if communication is sent to correspondent
        :return: None
        """
        partner = self.correspondent_id if correspondent else self.partner_id
        already_sent = self.env["partner.communication.job"].search(
            [
                ("partner_id", "=", partner.id),
                ("config_id", "=", communication_config.id),
                ("object_ids", "like", str(self.id)),
                ("state", "=", "done"),
            ]
        )
        if not already_sent:
            self.with_context({}).send_communication(
                communication_config, correspondent)
