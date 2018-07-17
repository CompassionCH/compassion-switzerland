# -*- coding: utf-8 -*-
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
    amount_due = fields.Integer(compute='_compute_due_invoices', store=True)
    months_due = fields.Integer(compute='_compute_due_invoices', store=True)

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
        for sponsorship in self:
            sponsorship.birthday_paid = self.env['sponsorship.gift'].search([
                ('sponsorship_id', '=', sponsorship.id),
                ('gift_date', '>=', fields.Date.to_string(today)),
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
            if contract.child_id.project_id.suspension != 'fund-suspended':
                invoice_lines = contract.invoice_line_ids.with_context(
                    lang='en_US').filtered(
                        lambda i: i.state == 'open' and
                        fields.Date.from_string(i.due_date) < this_month and
                        i.invoice_id.invoice_type == 'sponsorship'
                )
                contract.due_invoice_ids = invoice_lines.mapped('invoice_id')
                contract.amount_due = int(sum(invoice_lines.mapped(
                    'price_subtotal')))
                months = set()
                for invoice in invoice_lines.mapped('invoice_id'):
                    idate = fields.Date.from_string(invoice.date)
                    months.add((idate.month, idate.year))
                contract.months_due = len(months)

    @api.multi
    def _compute_period_paid(self):
        for contract in self:
            advance_billing = contract.group_id.advance_billing_months
            # Don't consider next year in the period to pay
            to_pay_period = min(date.today().month + advance_billing, 12)
            contract.period_paid = contract.months_paid >= to_pay_period

    @api.multi
    def compute_due_invoices(self):
        self._compute_due_invoices()
        return True

    def _get_sds_states(self):
        """ Add waiting_welcome state """
        res = super(RecurringContract, self)._get_sds_states()
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
        :param correspondant: put to false for sending to payer instead of
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
                communications += self.env['partner.communication.job'].create(
                    {
                        'config_id': communication.id,
                        'partner_id': partner.id,
                        'object_ids': self.env.context.get(
                            'default_object_ids', objects.ids),
                        'user_id': communication.user_id.id,
                    }
                )
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

    @api.model
    def send_daily_communication(self):
        """
        Prepare daily communications to send.
        - Welcome letters for started sponsorships since 10 days (only e-mail)
        - Birthday reminders
        """
        module = 'partner_communication_switzerland.'
        logger.info("Sponsorship Planned Communications started!")

        # Birthday Reminder
        logger.info("....Creating Birthday Reminder Communications")
        today = datetime.now()
        in_two_month = today + relativedelta(months=2)
        birthday = self.search([
            ('child_id.birthdate', 'like', in_two_month.strftime("%%-%m-%d")),
            '|', ('correspondent_id.birthday_reminder', '=', True),
            ('partner_id.birthday_reminder', '=', True),
            '|', ('correspondent_id.email', '!=', False),
            ('partner_id.email', '!=', False),
            ('state', '=', 'active'),
            ('type', 'like', 'S'),
            ('partner_id.ref', '!=', '1502623')  # if partner is not Demaurex
        ]).filtered(lambda c: not (
            c.child_id.project_id.lifecycle_ids and
            c.child_id.project_id.hold_s2b_letters)
        )
        config = self.env.ref(module + 'planned_birthday_reminder')
        comms = self.env['partner.communication.job']
        for sponsorship in birthday:

            # Send the communication to the correspondent in any case.
            correspondent = True

            # Send the communication to both the partner and correspondent
            # if the partner is the one who paid the gift.
            send_to_both = sponsorship.send_gifts_to == 'partner_id'

            try:
                comms += sponsorship.send_communication(config,
                                                        correspondent,
                                                        send_to_both)
            except:
                # In any case, we don't want to stop email generation!
                continue

        # send welcome activations letters
        welcome = self.env.ref(
            'partner_communication_switzerland.welcome_activation')
        to_send = self.env['recurring.contract'].search([
            ('activation_date', '>=', (datetime.today() - timedelta(days=1))),
            ('child_id', '!=', False)
        ])
        if to_send:
            to_send.send_communication(welcome, both=True).send()
            to_send.write({'sds_state': 'active'})

        logger.info("Sponsorship Planned Communications finished!")

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
        for sponsorship in self.search([
                ('state', 'in', ('active', 'mandate')),
                ('global_id', '!=', False),
                ('type', 'like', 'S'),
                '|',
                ('child_id.project_id.suspension', '!=', 'fund-suspended'),
                ('child_id.project_id.suspension', '=', False),
        ]):
            due = sponsorship.due_invoice_ids
            advance_billing = sponsorship.group_id.advance_billing_months
            if due and len(due) > 1 and not (advance_billing > 1 and len(
                    due) < 3):
                has_first_reminder = comm_obj.search_count([
                    ('config_id', 'in', [first_reminder_config.id,
                                         second_reminder_config.id]),
                    ('state', '=', 'done'),
                    ('object_ids', 'like', str(sponsorship.id)),
                    ('sent_date', '>=', fields.Date.to_string(fifty_ago)),
                    ('sent_date', '<', fields.Date.to_string(twenty_ago))
                ])
                if has_first_reminder:
                    second_reminder += sponsorship
                else:
                    has_first_reminder = comm_obj.search_count([
                        ('config_id', 'in', [first_reminder_config.id,
                                             second_reminder_config.id]),
                        ('state', '=', 'done'),
                        ('object_ids', 'like', str(sponsorship.id)),
                        ('sent_date', '>=', fields.Date.to_string(twenty_ago)),
                    ])
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
        report_obj = self.env['report']
        attachments = dict()
        partner_lang = self.mapped('correspondent_id')[0].lang
        product_name = products[0].with_context(lang=partner_lang).name
        attachments[product_name + '.pdf'] = [
            report,
            base64.b64encode(report_obj.get_pdf(
                self.ids, report,
                data={
                    'doc_ids': self.ids,
                    'product_ids': products.ids,
                    'background': background,
                }
            ))
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
        res = super(RecurringContract, self).action_sub_reject()
        no_sub_config = self.env.ref(
            'partner_communication_switzerland.planned_no_sub')
        self.send_communication(no_sub_config, correspondent=False)
        return res

    ##########################################################################
    #                            WORKFLOW METHODS                            #
    ##########################################################################
    @api.multi
    def contract_waiting_mandate(self):
        res = super(RecurringContract, self).contract_waiting_mandate()
        new_spons = self.filtered(lambda c: 'S' in c.type and not c.is_active)
        new_spons._new_dossier()
        new_spons.filtered(
            lambda s: s.correspondent_id.email and s.sds_state == 'draft' and
            s.partner_id.ref != '1502623').write({
                'sds_state': 'waiting_welcome',
                'sds_state_date': fields.Date.today()
            })
        if 'CSP' in self.name:
            module = 'partner_communication_switzerland.'
            selected_config = self.env.ref(module + 'csp_mail')
            self.send_communication(selected_config, correspondent=False)

        return res

    @api.multi
    def contract_waiting(self):
        # Waiting welcome for partners with e-mail (except Demaurex)
        welcome = self.filtered(
            lambda s: 'S' in s.type and s.sds_state == 'draft' and
            s.correspondent_id.email and s.partner_id.ref != '1502623')
        welcome.write({
            'sds_state': 'waiting_welcome'
        })

        mandates_valid = self.filtered(lambda c: c.state == 'mandate')
        res = super(RecurringContract, self).contract_waiting()
        self.filtered(
            lambda c: 'S' in c.type and not c.is_active and c not in
            mandates_valid
        )._new_dossier()

        if 'CSP' in self.name:
            module = 'partner_communication_switzerland.'
            selected_config = self.env.ref(module + 'csp_mail')
            self.send_communication(selected_config, correspondent=False)

        return res

    @api.multi
    def contract_active(self):
        """ Remove waiting reminders if any, and send welcome """
        self.env['partner.communication.job'].search([
            ('config_id.name', 'ilike', 'Waiting reminder'),
            ('state', '!=', 'done'),
            ('partner_id', 'in', self.mapped('partner_id').ids)
        ]).unlink()
        return super(RecurringContract, self).contract_active()

    @api.multi
    def send_welcome_letter(self):
        logger.info("Creating Welcome Letters Communications")
        config = self.env.ref(
            'partner_communication_switzerland.planned_welcome')
        self.send_communication(config, both=True).send()
        self.write({'sds_state': 'active'})
        return True

    @api.multi
    def contract_terminated(self):
        super(RecurringContract, self).contract_terminated()
        if self.child_id:
            self.child_id.sponsorship_ids[0].order_photo = False
        return True

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    @api.multi
    def _on_sponsorship_finished(self):
        super(RecurringContract, self)._on_sponsorship_finished()
        cancellation = self.env.ref(
            'partner_communication_switzerland.sponsorship_cancellation')
        no_sub = self.env.ref(
            'partner_communication_switzerland.planned_no_sub')
        self.filtered(
            lambda s: s.end_reason != '1' and not s.parent_id
        ).send_communication(cancellation, both=True)
        self.filtered(
            lambda s: s.end_reason != '1' and s.parent_id
        ).send_communication(no_sub, correspondent=False)

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
                    spo.send_communication(new_dossier)
                    spo.send_communication(new_dossier, correspondent=False)
                    continue

            spo.send_communication(new_dossier)

        for sub in sub_sponsorships:
            sub.send_communication(sub_proposal)
            if sub.correspondent_id.id != sub.partner_id.id:
                sub.send_communication(sub_proposal, correspondent=False)
