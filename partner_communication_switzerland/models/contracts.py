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
import logging
from datetime import timedelta, datetime

from openerp import api, models, fields, _

logger = logging.getLogger(__name__)


class RecurringContract(models.Model):
    """
    Add method to send all planned communication of sponsorships.
    """
    _inherit = ['recurring.contract', 'translatable.model']
    _name = 'recurring.contract'

    payment_type_attachment = fields.Char(
        compute='_compute_payment_type_attachment')

    def _compute_payment_type_attachment(self):
        for contract in self.with_context(lang='en_US'):
            phrase = ''
            payment_term = contract.payment_term_id.name
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

    def send_communication(self, communication, correspondent=True):
        """
        Sends a communication to selected sponsorships.
        :param communication: the communication config to use
        :param correspondant: put to false for sending to payer instead of
                              correspondent.
        :return: None
        """
        partner_field = 'correspondant_id' if correspondent else 'partner_id'
        partners = self.mapped(partner_field)
        for partner in partners:
            objects = self.filtered(
                lambda c: c.correspondant_id == partner.id if correspondent
                else c.partner_id == partner.id
            )
            self.env['partner.communication.job'].create({
                'config_id': communication.id,
                'partner_id': partner.id,
                'object_ids': objects.ids
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
        days_per_year = 365.24
        comp_month = '-' + str(today.month) + '-'
        logger.info("....Creating Anniversary Communications")
        for year in [1, 3, 5, 10, 15]:
            year_lookup = today - timedelta(days=year*days_per_year)
            comp_date = comp_month + year_lookup.strftime("%Y")
            anniversary = self.search([
                ('start_date', 'like', comp_date),
                ('state', '=', 'active'),
                ('S', 'in', 'type')
            ])
            config = self.env.ref(module + 'planned_anniversary_' + str(year))
            anniversary.send_communication(config)

        # Completion
        logger.info("....Creating Completion Communications")
        in_four_month = today + timedelta(days=int(30.4*4))
        comp_date = in_four_month.strftime("-%m-%Y")
        completion = self.search([
            ('child_id.completion_date', 'like', comp_date),
            ('state', '=', 'active'),
            ('S', 'in', 'type')
        ])
        config = self.env.ref(module + 'planned_completion')
        completion.send_communication(config)

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

        # Birthday Reminder
        logger.info("....Creating Birthday Reminder Communications")
        today = datetime.now()
        in_three_month = (today + timedelta(days=int(30.4*3))).replace(
            day=today.day)
        birthday = self.search([
            ('child_id.birthdate', '=', fields.Date.to_string(
                in_three_month)),
            ('correspondant_id.birthday_reminder', '=', True),
            ('state', '=', 'active'),
            ('S', 'in', 'type')
        ])
        config = self.env.ref(module + 'planned_birthday_reminder')
        birthday.send_communication(config)
