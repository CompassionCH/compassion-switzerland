# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import base64
import calendar
import logging
from datetime import datetime, date

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
        'account.invoice', compute='_compute_due_invoices'
    )
    amount_due = fields.Integer(compute='_compute_due_invoices')

    def _compute_payment_type_attachment(self):
        for contract in self:
            payment_mode = contract.with_context(
                lang='en_US').payment_mode_id.name
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

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def send_communication(self, communication, correspondent=True):
        """
        Sends a communication to selected sponsorships.
        :param communication: the communication config to use
        :param correspondant: put to false for sending to payer instead of
                              correspondent.
        :return: communication created recordset
        """
        partner_field = 'correspondant_id' if correspondent else 'partner_id'
        sponsorships = self.filtered(lambda s: 'S' in s.type)
        partners = sponsorships.mapped(partner_field)
        communications = self.env['partner.communication.job']
        for partner in partners:
            objects = sponsorships.filtered(
                lambda c: c.correspondant_id.id == partner.id if correspondent
                else c.partner_id.id == partner.id
            )
            communications += self.env['partner.communication.job'].create({
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

        # Completion
        logger.info("....Creating Completion Communications")
        in_three_month = today + relativedelta(months=3)
        start = in_three_month.replace(day=1)
        stop = in_three_month.replace(
            day=calendar.monthrange(in_three_month.year,
                                    in_three_month.month)[1])
        completion = self.search([
            ('child_id.completion_date', '>=', fields.Date.to_string(start)),
            ('child_id.completion_date', '<=', fields.Date.to_string(stop)),
            ('state', '=', 'active'),
            ('type', 'like', 'S')
        ])
        config = self.env.ref(module + 'planned_completion')
        completion.send_communication(config)
        logger.info("Sponsorship Planned Communications finished!")

    @api.model
    def send_daily_communication(self):
        """
        Prepare daily communications to send.
        - Welcome letters for started sponsorships since 10 days (only e-mail)
        - Birthday reminders
        - B2S letters that must be printed because e-mail is not read
          (deactivated for now)
        """
        module = 'partner_communication_switzerland.'

        # Welcome letter
        logger.info("Sponsorship Planned Communications started!")
        logger.info("....Creating Welcome Letters Communications")
        config = self.env.ref(module + 'planned_welcome')
        welcome_due = self.search([
            ('type', 'like', 'S'),
            ('partner_id.email', '!=', False),
            ('sds_state', '=', 'waiting_welcome'),
            ('color', '=', 4)
        ])
        welcome_due.send_communication(config)
        welcome_due.signal_workflow('mail_sent')

        # Birthday Reminder
        logger.info("....Creating Birthday Reminder Communications")
        today = datetime.now()
        in_two_month = (today + relativedelta(months=2)).replace(
            day=today.day)
        birthday = self.search([
            ('child_id.birthdate', '=like', in_two_month.strftime("%%-%m-%d")),
            ('correspondant_id.birthday_reminder', '=', True),
            ('state', '=', 'active'),
            ('type', 'like', 'S')
        ]).filtered(lambda c: not (
            c.child_id.project_id.lifecycle_ids and
            c.child_id.project_id.hold_s2b_letters)
        )
        config = self.env.ref(module + 'planned_birthday_reminder')
        comms = birthday.send_communication(config)
        # Remove communication for those who have no e-mail address
        comms.filtered(lambda c: not c.send_mode).unlink()

        # B2S Letters that must be printed (if not read after 10 days)
        # logger.info("....Creating B2S Printed Communications")
        ten_days_ago = today - relativedelta(days=10)
        # letters = self.env['correspondence'].search([
        #     ('state', '=', 'Published to Global Partner'),
        #     ('sent_date', '<', fields.Date.to_string(ten_days_ago)),
        #     ('letter_read', '=', False)
        # ])
        # letters.with_context(overwrite=True, comm_vals={
        #     'send_mode': 'physical',
        #     'auto_send': False,
        # }).send_communication()

        # First reminders not read must be printed for that still have
        # some amount due.
        first_reminders = self.env.ref(
            module + 'sponsorship_waiting_reminder_1') + self.env.ref(
            module + 'sponsorship_reminder_1')
        communications = self.env['partner.communication.job'].search([
            ('config_id', 'in', first_reminders.ids),
            ('send_mode', '=', 'digital'),
            ('sent_date', '=', fields.Date.to_string(ten_days_ago)),
            ('email_id.opened', '=', False)
        ])
        to_print = self.env['partner.communication.job']
        for comm in communications:
            sponsorships = comm.get_objects().filtered(
                lambda s: s.amount_due > s.total_amount)
            if sponsorships:
                to_print += comm
        to_print.write({'send_mode': 'physical', 'state': 'pending'})

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
            default_print_subject=False, default_auto_send=False)
        second_reminder = self.with_context(
            default_print_subject=False, default_auto_send=False)
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
        partner_lang = self.mapped('correspondant_id')[0].lang
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

    def get_bvr_attachment(self, gifts, other, background=False):
        """
        Get a BVR communication attachment for given products.
        :param gifts: product.product recordset
        :param other: product.product recordset
        :param background: wheter to print background or not
        :return: dict {attachment_name: [report_name, pdf_data]}
        """
        if gifts:
            report_gifts = 'report_compassion.bvr_gift_sponsorship'
            report_obj_gifts = self.env['report']
            attachments = dict()
            partner_lang = self.mapped('correspondant_id')[0].lang
            product_name = gifts[0].with_context(lang=partner_lang).name
            attachments[product_name + '.pdf'] = [
                report_gifts,
                base64.b64encode(report_obj_gifts.get_pdf(
                    self.ids, report_gifts,
                    data={
                        'doc_ids': self.ids,
                        'product_ids': gifts.ids,
                        'background': background,
                    }
                ))
            ]
        if other:
            report_other = 'report_compassion.3bvr_sponsorship'
            report_obj_other = self.env['report']
            attachments = dict()
            partner_lang = self.mapped('correspondant_id')[0].lang
            product_name = other[0].with_context(lang=partner_lang).name
            attachments[product_name + '.pdf'] = [
                report_other,
                base64.b64encode(report_obj_other.get_pdf(
                    self.ids, report_other,
                    data={
                        'doc_ids': self.ids,
                        'product_ids': other.ids,
                        'background': background,
                    }
                ))
            ]
        return attachments

    ##########################################################################
    #                            WORKFLOW METHODS                            #
    ##########################################################################
    @api.multi
    def contract_waiting_mandate(self):
        res = super(RecurringContract, self).contract_waiting_mandate()
        self.filtered(
            lambda c: 'S' in c.type and not c.is_active)._new_dossier()
        return res

    @api.multi
    def contract_waiting(self):
        res = super(RecurringContract, self).contract_waiting()
        self.filtered(
            lambda c: 'S' in c.type and not c.is_active)._new_dossier()
        return res

    @api.multi
    def no_sub(self):
        no_sub_config = self.env.ref(
            'partner_communication_switzerland.planned_no_sub')
        self.send_communication(no_sub_config, correspondent=False)
        return super(RecurringContract, self).no_sub()

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
            lambda s: s.end_reason != '1' and s.origin_id.type != 'sub'
        ).send_communication(cancellation)
        self.filtered(
            lambda s: s.end_reason != '1' and s.origin_id.type == 'sub'
        ).send_communication(no_sub)

    def _new_dossier(self):
        """
        Sends the dossier of the new sponsorship to both payer and
        correspondent. Separates the case where the new sponsosrship is a
        SUB proposal or if the sponsorship is selected by the sponsor.
        """
        module = 'partner_communication_switzerland.'
        selected_config = self.env.ref(module + 'planned_dossier')
        selected_payer_config = self.env.ref(module + 'planned_dossier_payer')
        selected_corr_config = self.env.ref(
            module + 'planned_dossier_correspondent')
        sub_proposal_config = self.env.ref(module + 'planned_sub_dossier')

        sub_proposal = self.filtered(
            lambda c: c.origin_id.name == 'SUB Sponsorship' and
            c.channel == 'direct')
        selected = self - sub_proposal

        for spo in selected:
            if spo.correspondant_id.id != spo.partner_id.id:
                corresp = spo.correspondant_id
                payer = spo.partner_id
                if corresp.contact_address != payer.contact_address:
                    spo.send_communication(selected_corr_config)
                    spo.send_communication(
                        selected_payer_config, correspondent=False)
                    continue

            spo.send_communication(selected_config)

        for sub in sub_proposal:
            sub.send_communication(sub_proposal_config)
            if sub.correspondant_id.id != sub.partner_id.id:
                sub.send_communication(
                    sub_proposal_config, correspondent=False)
