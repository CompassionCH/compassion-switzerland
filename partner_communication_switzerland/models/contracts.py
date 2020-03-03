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
import calendar
import logging
from datetime import datetime, date, timedelta

from dateutil.relativedelta import relativedelta

from odoo import api, models, fields, _
from odoo.addons.queue_job.job import job

logger = logging.getLogger(__name__)


class RecurringContract(models.Model):
    """
    Add method to send all planned communication of sponsorships.
    """
    _inherit = ['recurring.contract', 'translatable.model']
    _name = 'recurring.contract'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    order_photo = fields.Boolean(
        help='Indicates that the child has a new picture to be ordered with '
             'Smartphoto.')
    payment_type_attachment = fields.Char(
        compute='_compute_payment_type_attachment')
    birthday_paid = fields.Many2many(
        'sponsorship.gift', compute='_compute_birthday_paid')
    due_invoice_ids = fields.Many2many(
        'account.invoice', compute='_compute_due_invoices', store=True
    )
    period_paid = fields.Boolean(
        compute='_compute_period_paid',
        help='Tells if the advance billing period is already paid'
    )
    months_due = fields.Integer(compute='_compute_due_invoices', store=True)
    welcome_active_letter_sent = fields.Boolean(
        "Welcome letters sent",
        default=False, help="Tells if welcome active letter has been sent")
    send_introduction_letter = fields.Boolean(
        string='Send B2S intro letter to sponsor', default=True)
    origin_type = fields.Selection(related='origin_id.type')
    sds_state = fields.Selection(selection_add=[
        ('waiting_welcome', _('Waiting welcome'))])

    # this field is used to help the xml views to get the type of origin_id

    @api.onchange('origin_id')
    def _do_not_send_letter_to_transfer(self):
        if self.origin_id.type == 'transfer':
            self.send_introduction_letter = False

    def _compute_payment_type_attachment(self):
        for contract in self:
            payment_mode = contract.with_context(
                lang='en_US').payment_mode_id.name or ''
            if payment_mode == 'Permanent Order':
                phrase = _('1 payment slip to set up a standing order ('
                           'monthly payment of the sponsorship)')
            elif 'LSV' in payment_mode or 'Postfinance' in payment_mode:
                if contract.state == 'mandate':
                    phrase = _("1 LSV or Direct Debit authorization form to "
                               "fill in if you don't already have done it!")
                else:
                    phrase = _("We will continue to withdraw the amount for "
                               "the sponsorship from your account.")
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
            sponsorship.birthday_paid = self.env['sponsorship.gift'].search([
                ('sponsorship_id', '=', sponsorship.id),
                ('gift_date', '>=', fields.Date.to_string(since_six_months)),
                ('gift_date', '<', fields.Date.to_string(in_three_months)),
                ('sponsorship_gift_type', '=', 'Birthday'),
            ])

    @api.depends('invoice_line_ids', 'invoice_line_ids.state')
    def _compute_due_invoices(self):
        """
        Useful for reminders giving open invoices in the past.
        """
        this_month = date.today().replace(day=1)
        for contract in self:
            if contract.child_id.project_id.suspension != \
                    'fund-suspended' and contract.type != 'SC':
                invoice_lines = contract.invoice_line_ids.with_context(
                    lang='en_US').filtered(
                    lambda i: i.state == 'open' and fields.Date.
                        from_string(i.due_date) < this_month and
                        i.invoice_id.invoice_type == 'sponsorship')
                contract.due_invoice_ids = invoice_lines.mapped('invoice_id')
                contract.amount_due = int(sum(invoice_lines.mapped(
                    'price_subtotal')))
                months = set()
                for invoice in invoice_lines.mapped('invoice_id'):
                    idate = fields.Date.from_string(invoice.date)
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

    def _get_sds_states(self):
        """ Add waiting_welcome state """
        res = super()._get_sds_states()
        res.insert(1, ('waiting_welcome', _('Waiting welcome')))
        return res

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def send_communication(self, communication, correspondent=True,
                           both=False):
        """
        Sends a communication to selected sponsorships.
        :param communication: the communication config to use
        :param correspondent: put to false for sending to payer instead of
                              correspondent.
        :param both:          send to both correspondent and payer
                              (overrides the previous parameter)
        :return: communication created recordset
        """
        partner_field = 'correspondent_id' if correspondent else 'partner_id'
        partners = self.mapped(partner_field)
        communications = self.env['partner.communication.job']
        if both:
            for contract in self:
                communications += self.env['partner.communication.job'].create(
                    {
                        'config_id': communication.id,
                        'partner_id': contract.partner_id.id,
                        'object_ids': self.env.context.get(
                            'default_object_ids', contract.id),
                        'user_id': communication.user_id.id,
                    })
                if contract.correspondent_id != contract.partner_id:
                    communications += self.env[
                        'partner.communication.job'].create({
                            'config_id': communication.id,
                            'partner_id': contract.correspondent_id.id,
                            'object_ids': self.env.context.get(
                                'default_object_ids', contract.id),
                            'user_id': communication.user_id.id,
                        })
        else:
            for partner in partners:
                objects = self.filtered(
                    lambda c: c.correspondent_id == partner if correspondent
                    else c.partner_id == partner
                )
                communications += self.env['partner.communication.job']\
                    .create({
                        'config_id': communication.id,
                        'partner_id': partner.id,
                        'object_ids': self.env.context.get(
                            'default_object_ids', objects.ids),
                        'user_id': communication.user_id.id,
                    })
        return communications

    @api.model
    def send_monthly_communication(self):
        """ Go through active sponsorships and send all planned
        communications.
        """
        module = 'partner_communication_switzerland.'
        logger.info("Sponsorship Planned Communications started!")

        # Sponsorship anniversary
        today = datetime.now()
        logger.info("....Creating Anniversary Communications")
        for year in [1, 3, 5, 10, 15]:
            year_lookup = today - relativedelta(years=year)
            start = year_lookup.replace(day=1)
            stop = year_lookup.replace(
                day=calendar.monthrange(year_lookup.year,
                                        year_lookup.month)[1])
            anniversary = self.search([
                ('start_date', '>=', fields.Date.to_string(start)),
                ('start_date', '<=', fields.Date.to_string(stop)),
                ('state', '=', 'active'),
                ('type', 'like', 'S')
            ])
            config = self.env.ref(module + 'planned_anniversary_' + str(year))
            anniversary.send_communication(config)

        # Write & Pray reminders after 3 months of activation
        logger.info("....Creating Write&Pray Reminders")
        three_month_ago = today - relativedelta(months=3)
        four_month_ago = today - relativedelta(months=4)
        wrpr_sponsorships = self.search([
            ('state', '=', 'active'),
            ('type', '=', 'SC'),
            ('activation_date', '<', fields.Date.to_string(three_month_ago)),
            ('activation_date', '>=', fields.Date.to_string(four_month_ago)),
        ])
        config = self.env.ref(module + 'sponsorship_wrpr_reminder')
        for sponsorship in wrpr_sponsorships:
            if not sponsorship.sponsor_letter_ids:
                sponsorship.send_communication(config)

    @api.model
    def send_daily_communication(self):
        """
        Prepare daily communications to send.
        - Welcome letters for started sponsorships since 1 day (only e-mail)
        - Birthday reminders
        """
        logger.info("Sponsorship Planned Communications started!")

        logger.info("....Creating Birthday Reminder Communications")
        self._send_reminders_for_birthday_in_1day_or_2months()

        logger.info("....Send Welcome Activations Letters")
        self._send_welcome_active_letters_for_activated_sponsorships()

        logger.info("Sponsorship Planned Communications finished!")

    @api.model
    def _send_reminders_for_birthday_in_1day_or_2months(self):
        module = 'partner_communication_switzerland.'
        logger.info("....Creating Birthday Reminder Communications")
        today = datetime.now()

        in_two_month = today + relativedelta(months=2)
        sponsorships_with_birthday_in_two_months = \
            self._get_sponsorships_with_child_birthday_on(in_two_month)
        self._send_birthday_reminders(
            sponsorships_with_birthday_in_two_months,
            self.env.ref(module + 'planned_birthday_reminder')
        )

        tomorrow = today + relativedelta(days=1)
        sponsorships_with_birthday_tomorrow = \
            self._get_sponsorships_with_child_birthday_on(tomorrow)

        sponsorships_to_avoid = self.env['recurring.contract']

        for sponsorship in sponsorships_with_birthday_tomorrow:
            sponsorship_correspondences = self.env['correspondence'].search_count([
                ('sponsorship_id', '=', sponsorship.id),
                ('direction', '=', "Supporter To Beneficiary"),
                ('scanned_date', '>=', fields.Date.to_string(
                    datetime.now() - relativedelta(months=2)))
            ])

            if sponsorship_correspondences:
                sponsorships_to_avoid += sponsorship
                continue

            sponsorship_gifts = self.env['sponsorship.gift'].search([
                ('sponsorship_id', '=', sponsorship.id),
                ('date_partner_paid', '>=',
                 fields.Date.to_string(datetime.now() - relativedelta(months=2)))
            ])

            if sponsorship_gifts:
                sponsorships_to_avoid += sponsorship

        self._send_birthday_reminders(
            sponsorships_with_birthday_tomorrow - sponsorships_to_avoid,
            self.env.ref(module + 'birthday_remainder_1day_before')
        )

    @api.model
    def _send_birthday_reminders(self, sponsorships, communication):
        communication_jobs = self.env['partner.communication.job']
        for sponsorship in sponsorships:
            send_to_partner_as_he_paid_the_gift = \
                sponsorship.send_gifts_to == 'partner_id'
            try:
                communication_jobs += sponsorship.send_communication(
                    communication,
                    correspondent=True,
                    both=send_to_partner_as_he_paid_the_gift
                )
            except Exception:
                # In any case, we don't want to stop email generation!
                logger.error("Error during birthday reminder: ", exc_info=True)

    @api.model
    def _get_sponsorships_with_child_birthday_on(self, birth_day):
        corresp_compass_tag = 'partner_compassion.res_partner_category_corresp_compass'
        return self.search([
            ('child_id.birthdate', 'like', birth_day.strftime("%%-%m-%d")),
            '|', ('correspondent_id.birthday_reminder', '=', True),
            ('partner_id.birthday_reminder', '=', True),
            '|', ('correspondent_id.email', '!=', False),
            ('partner_id.email', '!=', False),
            ('state', '=', 'active'),
            ('type', 'like', 'S'),
            ('partner_id.ref', '!=', '1502623'),  # if partner is not Demaurex
            ('partner_id.category_id', 'not in', self.env.ref(corresp_compass_tag).ids)
        ]).filtered(lambda c: not (
            c.child_id.project_id.lifecycle_ids and
            c.child_id.project_id.hold_s2b_letters))

    @api.model
    def _send_welcome_active_letters_for_activated_sponsorships(self):
        welcome = self.env.ref(
            'partner_communication_switzerland.welcome_activation')
        yesterday = fields.Datetime.to_string(
            datetime.today() - timedelta(days=1))
        five_days_diff = fields.Datetime.to_string(
            datetime.today() - timedelta(days=5))
        # problem -> all records don't have field welcome_active_letter_sent
        to_send = self.env['recurring.contract'].search([
            ('activation_date', '<=', yesterday),
            ('start_date', '<=', five_days_diff),
            ('child_id', '!=', False),
            ('type', '=', 'S'),
            ('origin_id.type', '!=', 'transfer'),
            ('welcome_active_letter_sent', '=', False)
        ])
        if to_send:
            to_send.send_communication(welcome, both=True).send()
            to_send.write({
                'sds_state': 'active',
                'welcome_active_letter_sent': True
            })

    @api.model
    def send_sponsorship_reminders(self):
        logger.info("Creating Sponsorship Reminders")
        today = datetime.now()
        first_reminder_config = self.env.ref(
            'partner_communication_switzerland.sponsorship_reminder_1')
        second_reminder_config = self.env.ref(
            'partner_communication_switzerland.sponsorship_reminder_2')
        first_reminder = self.with_context(
            default_print_subject=False, default_auto_send=False,
            default_print_header=True
        )
        second_reminder = self.with_context(
            default_print_subject=False, default_auto_send=False,
            default_print_header=True
        )
        fifty_ago = today - relativedelta(days=50)
        twenty_ago = today - relativedelta(days=20)
        comm_obj = self.env['partner.communication.job']
        search_domain = [
            ('state', 'in', ('active', 'mandate')),
            ('global_id', '!=', False),
            ('type', 'like', 'S'),
            '|',
            ('child_id.project_id.suspension', '!=', 'fund-suspended'),
            ('child_id.project_id.suspension', '=', False)
        ]
        # Recompute due invoices of multi-months payers, because
        # due months are only recomputed when new invoices are generated
        # which could take up to one year for yearly payers.
        multi_month = self.search(
            search_domain + [('group_id.advance_billing_months', '>', 3)]
        )
        multi_month.compute_due_invoices()
        for sponsorship in self.search(
                search_domain + [('months_due', '>', 1)]
        ):
            reminder_search = [
                ('config_id', 'in', [first_reminder_config.id,
                                     second_reminder_config.id]),
                ('state', '=', 'done'),
                ('object_ids', 'like', str(sponsorship.id))
            ]
            # Look if first reminder was sent previous month (send second
            # reminder in that case)
            has_first_reminder = comm_obj.search_count(
                reminder_search +
                [('sent_date', '>=', fields.Date.to_string(fifty_ago)),
                 ('sent_date', '<', fields.Date.to_string(twenty_ago))]
            )
            if has_first_reminder:
                second_reminder += sponsorship
            else:
                # Send first reminder only if one was not already sent less
                # than twenty days ago
                has_first_reminder = comm_obj.search_count(
                    reminder_search +
                    [('sent_date', '>=', fields.Date.to_string(twenty_ago))]
                )
                if not has_first_reminder:
                    first_reminder += sponsorship
        first_reminder.send_communication(first_reminder_config,
                                          correspondent=False)
        second_reminder.send_communication(second_reminder_config,
                                           correspondent=False)
        logger.info("Sponsorship Reminders created!")
        return True

    def get_bvr_gift_attachment(self, products, background=False):
        """
        Get a BVR communication attachment for given gift products.
        :param products: product.product recordset
        :param background: wheter to print background or not
        :return: dict {attachment_name: [report_name, pdf_data]}
        """
        report = 'report_compassion.bvr_gift_sponsorship'
        attachments = dict()
        partner_lang = self.mapped('correspondent_id')[0].lang
        product_name = products[0].with_context(lang=partner_lang).name
        report_ref = self.env.ref('report_compassion.report_bvr_gift_sponsorship')
        pdf_data = report_ref.report_action(self, data={
            'doc_ids': self.ids,
            'product_ids': products.ids,
            'background': background,
        })
        attachments[product_name + '.pdf'] = [
            report,
            base64.encodebytes(report_ref.render_qweb_pdf(
                pdf_data['data']['doc_ids'], pdf_data['data']))
        ]
        return attachments

    def intersect(self, other):
        """ Utility to intersect from template """
        return self & other

    def must_pay_next_year(self):
        """ Utility to tell if sponsorship must be paid next year. """
        return max(self.mapped('months_paid')) < 24

    @api.multi
    def action_sub_reject(self):
        res = super().action_sub_reject()
        no_sub_config = self.env.ref(
            'partner_communication_switzerland.planned_no_sub')
        self.send_communication(no_sub_config, correspondent=False)
        return res

    ##########################################################################
    #                            WORKFLOW METHODS                            #
    ##########################################################################
    @api.multi
    def contract_waiting_mandate(self):
        res = super().contract_waiting_mandate()
        new_spons = self.filtered(lambda c: 'S' in c.type and not c.is_active)
        new_spons._new_dossier()
        new_spons.filtered(
            lambda s: s.correspondent_id.email and s.sds_state == 'draft' and
            s.partner_id.ref != '1502623' and not
            s.welcome_active_letter_sent).write({
                'sds_state': 'waiting_welcome', 'sds_state_date':
                fields.Date.today()})
        csp = self.filtered(
            lambda s: '6014' in s.mapped(
                'contract_line_ids.product_id.property_account_income_id.code')
        )
        if csp:
            module = 'partner_communication_switzerland.'
            selected_config = self.env.ref(module + 'csp_mail')
            csp.send_communication(selected_config, correspondent=False)

        return res

    @api.multi
    def contract_waiting(self):
        # Waiting welcome for partners with e-mail (except Demaurex)
        welcome = self.filtered(
            lambda s: 'S' in s.type and s.sds_state == 'draft' and
                      s.correspondent_id.email and s.partner_id.ref !=
                      '1502623' and not s.welcome_active_letter_sent
        )
        welcome.write({
            'sds_state': 'waiting_welcome'
        })

        mandates_valid = self.filtered(lambda c: c.state == 'mandate')
        res = super().contract_waiting()
        self.filtered(
            lambda c: 'S' in c.type and not c.is_active and c not in
                      mandates_valid
        )._new_dossier()

        csp = self.filtered(lambda s: 'CSP' in s.name)
        if csp:
            module = 'partner_communication_switzerland.'
            selected_config = self.env.ref(module + 'csp_mail')
            csp.send_communication(selected_config, correspondent=False)

        return res

    @api.multi
    def contract_active(self):
        """ Remove waiting reminders if any, and send welcome """
        self.env['partner.communication.job'].search([
            ('config_id.name', 'ilike', 'Waiting reminder'),
            ('state', '!=', 'done'),
            ('partner_id', 'in', self.mapped('partner_id').ids)
        ]).unlink()
        # This prevents sending welcome e-mail if it's already active
        self.write({'sds_state': 'active'})
        # Send new dossier for write&pray sponsorships
        self.filtered(lambda s: s.type == 'SC').send_communication(
            self.env.ref('partner_communication_switzerland'
                         '.sponsorship_dossier_wrpr'))
        return super().contract_active()

    @api.multi
    def send_welcome_letter(self):
        logger.info("Creating Welcome Letters Communications")
        config = self.env.ref(
            'partner_communication_switzerland.planned_welcome')

        if not self.origin_id or self.origin_id.type != 'transfer':
            communication = self.send_communication(config, both=True)
            self.with_delay(
                eta=datetime.now() + relativedelta(minutes=30)) \
                .send_welcome_communication(communication)

        self.write({'sds_state': 'active'})
        return True

    @job
    def send_welcome_communication(self, communication):
        self.ensure_one()
        communication.send()
        return True

    @api.multi
    def contract_terminated(self):
        super().contract_terminated()
        if self.child_id:
            self.child_id.sponsorship_ids[0].order_photo = False
        return True

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    @api.multi
    def _on_sponsorship_finished(self):
        super()._on_sponsorship_finished()
        cancellation = self.env.ref(
            'partner_communication_switzerland.sponsorship_cancellation')
        no_sub = self.env.ref(
            'partner_communication_switzerland.planned_no_sub')
        # Send cancellation for regular sponsorships
        self.filtered(
            lambda s: s.end_reason != '1' and not s.parent_id
        ).send_communication(cancellation, both=True)
        # Send NO SUB letter if activation is less than two weeks ago
        # otherwise send Cancellation letter for SUB sponsorships
        activation_limit = date.today() - relativedelta(days=15)
        self.filtered(
            lambda s: s.end_reason != '1' and s.parent_id
            and (s.activation_date and fields.Date.
                 from_string(s.activation_date) < activation_limit)
        ).send_communication(cancellation, correspondent=False)
        self.filtered(
            lambda s: s.end_reason != '1' and s.parent_id and
            (not s.activation_date or fields.Date.
                from_string(s.activation_date) >= activation_limit)).\
            send_communication(no_sub, correspondent=False)

    def _new_dossier(self):
        """
        Sends the dossier of the new sponsorship to both payer and
        correspondent. Separates the case where the new sponsorship is a
        SUB proposal or if the sponsorship is selected by the sponsor.
        """
        module = 'partner_communication_switzerland.'
        new_dossier = self.env.ref(module + 'planned_dossier')

        sub_sponsorships = self.filtered(lambda c: c.parent_id)
        sub_proposal = self.env.ref(module + 'planned_sub_dossier')
        selected = self - sub_sponsorships

        for spo in selected:
            if spo.correspondent_id.id != spo.partner_id.id:
                corresp = spo.correspondent_id
                payer = spo.partner_id
                if corresp.contact_address != payer.contact_address:
                    spo._send_new_dossier(new_dossier)
                    spo._send_new_dossier(new_dossier, correspondent=False)
                    continue

            spo._send_new_dossier(new_dossier)

        for sub in sub_sponsorships:
            sub._send_new_dossier(sub_proposal)
            if sub.correspondent_id.id != sub.partner_id.id:
                sub._send_new_dossier(sub_proposal, correspondent=False)

    def _send_new_dossier(self, communication_config, correspondent=True):
        """
        Sends the New Dossier if it wasn't already sent for this sponsorship.
        :param communication_config: Communication Config record to search.
        :param correspondent: True if communication is sent to correspondent
        :return: None
        """
        partner = self.correspondent_id if correspondent else self.partner_id
        already_sent = self.env['partner.communication.job'].search([
            ('partner_id', '=', partner.id),
            ('config_id', '=', communication_config.id),
            ('object_ids', 'like', str(self.id)),
            ('state', '=', 'done')
        ])
        if not already_sent:
            self.send_communication(communication_config, correspondent)
