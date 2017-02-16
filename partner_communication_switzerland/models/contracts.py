# -*- encoding: utf-8 -*-
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
from datetime import datetime

from dateutil.relativedelta import relativedelta

from openerp import api, models, fields, _

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

    def _compute_payment_type_attachment(self):
        for contract in self:
            payment_term = contract.with_context(
                lang='en_US').payment_term_id.name
            if payment_term == 'Permanent Order':
                phrase = _('1 payment slip to set up a standing order ('
                           'monthly payment of the sponsorship)')
            elif 'LSV' in payment_term or 'Postfinance' in payment_term:
                if contract.state == 'mandate':
                    phrase = _("1 LSV or Direct Debit authorization form to "
                               "fill in if you don't already have done it!")
                else:
                    phrase = _("We will continue to withdraw the amount for "
                               "the sponsorship from your account.")
            else:
                freq = contract.payment_term_id.recurring_value
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

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def send_communication(self, communication, correspondent=True):
        """
        Sends a communication to selected sponsorships.
        :param communication: the communication config to use
        :param correspondant: put to false for sending to payer instead of
                              correspondent.
        :return: None
        """
        partner_field = 'correspondant_id' if correspondent else 'partner_id'
        sponsorships = self.filtered(lambda s: 'S' in s.type)
        partners = sponsorships.mapped(partner_field)
        for partner in partners:
            objects = sponsorships.filtered(
                lambda c: c.correspondant_id.id == partner.id if correspondent
                else c.partner_id.id == partner.id
            )
            self.env['partner.communication.job'].create({
                'config_id': communication.id,
                'partner_id': partner.id,
                'object_ids': objects.ids,
            })

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
        module = 'partner_communication_switzerland.'

        # Welcome letter
        logger.info("Sponsorship Planned Communications started!")
        logger.info("....Creating Welcome Letters Communications")
        config = self.env.ref(module + 'planned_welcome')
        welcome_due = self.search([
            ('sds_state', '=', 'waiting_welcome'),
            ('color', '=', 4)
        ])
        welcome_due.send_communication(config)
        welcome_due.signal_workflow('mail_sent')

        # Birthday Reminder
        logger.info("....Creating Birthday Reminder Communications")
        today = datetime.now()
        # in_two_month = (today + relativedelta(months=2)).replace(
        #     day=today.day)
        # birthday = self.search([
        #     ('child_id.birthdate', 'like',
        #      in_two_month.strftime("%m-%d")),
        #     ('correspondant_id.birthday_reminder', '=', True),
        #     ('state', '=', 'active'),
        #     ('type', 'like', 'S')
        # ]).filtered(lambda c: not c.child_id.project_id.hold_s2b_letters)
        # config = self.env.ref(module + 'planned_birthday_reminder')
        # TODO Reactivate in March
        # birthday.send_communication(config)

        # B2S Letters that must be printed (if not read after 10 days)
        logger.info("....Creating B2S Printed Communications")
        ten_days_ago = today - relativedelta(days=10)
        letters = self.env['correspondence'].search([
            ('state', '=', 'Published to Global Partner'),
            '|',
            ('sent_date', '<', fields.Date.to_string(ten_days_ago)),
            ('sent_date', '=', False),
            ('letter_read', '=', False)
        ])
        letters.with_context(overwrite=True, comm_vals={
            'send_mode': 'physical',
            'auto_send': False,
        }).send_communication()
        logger.info("Sponsorship Planned Communications finished!")

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
                self, report,
                data={
                    'doc_ids': self.ids,
                    'product_ids': products.ids,
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
        self.filtered(
            lambda c: 'S' in c.type and not c.is_active)._new_dossier()
        return super(RecurringContract, self).contract_waiting_mandate()

    @api.multi
    def contract_waiting(self):
        self.filtered(
            lambda c: 'S' in c.type and not c.is_active)._new_dossier()
        return super(RecurringContract, self).contract_waiting()

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
        self.filtered(
            lambda s: s.end_reason != '1').send_communication(cancellation)

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
