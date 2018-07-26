# -*- coding: utf-8 -*-
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

from odoo import api, models, fields, _

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    """
    Add method to send all planned communication of sponsorships.
    """
    _name = 'res.partner'
    _inherit = ['res.partner', 'translatable.model']

    letter_delivery_preference = fields.Selection(
        selection='_get_delivery_preference',
        default='auto_digital',
        required=True,
        help='Delivery preference for Child Letters',
    )
    thankyou_preference = fields.Selection(
        compute='_compute_thankyou_preference', store=True
    )
    tax_receipt_preference = fields.Selection(
        selection='_get_delivery_preference',
        compute='_compute_tax_receipt_preference', store=True
    )
    is_new_donor = fields.Boolean(compute='_compute_new_donor')

    @api.multi
    def _compute_salutation(self):
        company = self.filtered(
            lambda p: not (p.title and p.firstname and not p.is_company))
        for p in company:
            p.salutation = _("Dear friends of compassion")
            p.short_salutation = p.salutation
        super(ResPartner, self - company)._compute_salutation()

    @api.multi
    @api.depends('thankyou_letter')
    def _compute_thankyou_preference(self):
        """
        Converts old preference into communication preference.
        """
        thankyou_mapping = {
            'no': 'none',
            'default': 'auto_digital',
            'paper': 'physical'
        }
        for partner in self:
            partner.thankyou_preference = thankyou_mapping[
                partner.thankyou_letter]

    @api.multi
    @api.depends('tax_certificate', 'birthdate_date')
    def _compute_tax_receipt_preference(self):
        """
        Converts old preference into communication preference.
        """
        receipt_mapping = {
            'no': 'none',
            'paper': 'physical'
        }

        def _get_default_pref(partner):
            if partner.birthdate_date:
                today = date.today()
                birthday = fields.Date.from_string(partner.birthdate_date)
                if (today - birthday).days > 365 * 60:
                    # Old people get paper
                    return 'physical'
            return 'digital'

        for partner in self:
            partner.tax_receipt_preference = receipt_mapping.get(
                partner.tax_certificate,
                _get_default_pref(partner)
            )

    @api.multi
    def _compute_new_donor(self):
        invl_obj = self.env['account.invoice.line'].with_context(lang='en_US')
        for partner in self:
            donation_invl = invl_obj.search([
                ('partner_id', '=', partner.id),
                ('state', '=', 'paid'),
                ('product_id.categ_name', '!=', "Sponsorship")
            ])
            payments = donation_invl.mapped('last_payment')
            new_donor = len(payments) < 2 and not partner.has_sponsorships
            partner.is_new_donor = new_donor

    @api.model
    def generate_tax_receipts(self):
        """
        Generate all tax receipts of last year.
        Called once a year to prepare all communications
        :return: recordset of partner.communication.job
        """
        # Select partners that made donations last year (query is faster)
        account_id = self.env['account.account'].search([
            ('code', '=', '1050')]).id
        journal_id = self.env['account.journal'].search([
            ('code', '=', 'SAJ')]).id
        today = date.today()
        start_date = today.replace(today.year - 1, 1, 1)
        end_date = today.replace(today.year - 1, 12, 31)
        config = self.env.ref('partner_communication_switzerland.'
                              'tax_receipt_config')
        self.env.cr.execute("""
            SELECT DISTINCT m.partner_id
            FROM account_move_line m JOIN res_partner p ON m.partner_id = p.id
            WHERE m.account_id = %s
            AND m.journal_id != %s
            AND m.credit > 0
            AND p.tax_certificate != 'no'
            AND m.date BETWEEN %s AND %s
            AND NOT EXISTS (
              SELECT id FROM partner_communication_job
              WHERE partner_id = p.id
              AND config_id = %s AND state IN ('sent','pending') AND date > %s
            )
        """, [account_id, journal_id, fields.Date.to_string(start_date),
              fields.Date.to_string(end_date), config.id, end_date])

        partner_ids = [r[0] for r in self.env.cr.fetchall()]
        total = len(partner_ids)
        count = 1
        for partner_id in partner_ids:
            _logger.info("Generating tax receipts: {}/{}".format(
                count, total))
            self.env['partner.communication.job'].create({
                'config_id': config.id,
                'partner_id': partner_id,
                'object_ids': partner_id,
                'user_id': config.user_id.id,
                'show_signature': True,
                'print_subject': False
            })
            # Commit at each creation of communication to avoid starting all
            # again in case the job failed
            self.env.cr.commit()    # pylint: disable=invalid-commit
            count += 1
        return True

    @api.multi
    def sms_send_step1_confirmation(self, child_request):
        # Override to use a communication instead of message_post
        config = self.env.ref('partner_communication_switzerland.'
                              'sms_registration_confirmation_1')
        child_request.sponsorship_id.send_communication(config)
        return True

    @api.multi
    def sms_send_step2_confirmation(self, child_request):
        # Override to use a communication instead of message_post
        config = self.env.ref('partner_communication_switzerland.'
                              'sms_registration_confirmation_2')
        child_request.sponsorship_id.send_communication(config)
        return True


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.multi
    def _compute_signature_letter(self):
        """ Translate country in Signature (for Compassion Switzerland) """
        for user in self:
            employee = user.employee_ids
            signature = ''
            if len(employee) == 1:
                signature += employee.name + '<br/>'
                if employee.department_id:
                    signature += employee.department_id.name + '<br/>'
            signature += user.company_id.name.split(' ')[0] + ' '
            signature += user.company_id.country_id.name
            user.signature_letter = signature
