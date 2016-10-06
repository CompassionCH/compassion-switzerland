# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Roman Zoller, Emanuel Cino, Michael Sandoz
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import models, fields, api


class Correspondence(models.Model):
    _inherit = 'correspondence'

    email_id = fields.Many2one('mail.mail', 'E-mail')
    email_sent_date = fields.Datetime(
        'E-mail sent',
        related='email_id.sent_date', store=True)
    email_read = fields.Boolean(
        compute='_compute_email_read', store=True
    )

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.multi
    @api.depends('email_id.state')
    def _compute_email_read(self):
        for letter in self:
            email = letter.email_id
            if email and email.state == 'received':
                letter.email_read = True
            else:
                letter.email_read = False

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.one
    def process_letter(self):
        """ Method called when B2S letter is Published. This will send the
            letter to the sponsor via Sendgrid e-mail.

            :param: download_image: Set to False to avoid downloading the
                                    letter image from GMC and attaching it.
        """
        composed_ok = super(Correspondence, self).process_letter()
        partner = self.correspondant_id
        if partner.email and partner.delivery_preference == 'digital' and not\
                self.email_id:
            template = False
            if self.partner_needs_explanations():
                template = self.env.ref('sbc_email.change_system')
            else:
                template = self.env.ref('sbc_email.new_letter')

            # Create email
            email_vals = {
                'recipient_ids': [(4, partner.id)],
            }
            # EXCEPTION FOR DEMAUREX : send to Delafontaine
            if partner.ref == '1502623':
                email_vals['email_to'] = 'eric.delafontaine@aligro.ch'
                del email_vals['recipient_ids']

            self.email_id = self.env['mail.compose.message'].with_context(
                lang=partner.lang).create_emails(
                template, self.id, email_vals)

            if self._can_auto_send() and composed_ok:
                self.email_id.send_sendgrid()

    def get_image(self, user=None):
        """ Mark the e-mail as read. """
        data = super(Correspondence, self).get_image(user)
        # User is None if the sponsor called the service.
        if self.email_id and self.email_id.state == 'sent' and user is None:
            self.email_id.state = 'received'
        return data

    @api.multi
    def partner_needs_explanations(self):
        """ Returns true if the partner never received explanations
            about the new correspondence system. The partner should have a
            sponsorship that began before the transition of system.
        """
        self.ensure_one()
        partner_id = self.correspondant_id.id
        oldest_sponsorship = self.env['recurring.contract'].search([
            ('correspondant_id', '=', partner_id),
            ('type', 'like', 'S')], order='activation_date asc', limit=1)
        activation_date = fields.Date.from_string(
            oldest_sponsorship.activation_date)
        transition_date = fields.Date.from_string('2016-01-25')
        other_letters = self.search([
            ('correspondant_id', '=', partner_id),
            ('direction', '=', 'Beneficiary To Supporter'),
            ('id', '!=', self.id)])
        return (activation_date < transition_date and not other_letters)

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _can_auto_send(self):
        """ Tells if we can automatically send the letter by e-mail or should
        require manual validation before.
        """
        self.ensure_one()
        valid = False
        partner_langs = self.supporter_languages_ids
        common = partner_langs & self.beneficiary_language_ids
        if common:
            types = self.communication_type_ids.mapped('name')
            valid = (
                self.sponsorship_id.state == 'active' and
                'Final Letter' not in types and
                self.translation_language_id in partner_langs and
                self.correspondant_id.ref != '1502623'  # Demaurex
            )
        else:
            # TODO Until new translation platform is working: we have
            # to manually verify letters.
            # Check that the translation is filled
            # valid = self.page_ids.filtered('translated_text') and \
            #     self.translation_language_id in partner_langs

            # TODO Activate when most letters are hand-translated
            # self.b2s_layout_id = self.env.ref('sbc_compassion.b2s_l6')
            # self.attach_original()
            # self.compose_letter_image()

            valid = False
        return valid
