# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Roman Zoller
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import models, fields, api


class SponsorshipCorrespondence(models.Model):
    _inherit = 'sponsorship.correspondence'

    email_id = fields.Many2one('mail.mail')
    email_sent_date = fields.Datetime(
        related='email_id.sent_date', store=True)

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.one
    def process_letter(self):
        """ Method called when B2S letter is Published. This will send the
            letter to the sponsor via Sendgrid e-mail.
        """
        super(SponsorshipCorrespondence, self).process_letter()
        partner = self.correspondant_id
        if partner.email and partner.delivery_preference == 'digital':
            template = False
            if self.partner_needs_explanations():
                template = self.env.ref('sbc_email.change_system')
            else:
                template = self.env.ref('sbc_email.new_letter')

            # Create email
            from_address = self.env['ir.config_parameter'].get_param(
                'sbc_email.from_address')
            to_address = partner.email
            # EXCEPTION FOR DEMAUREX : send to Delafontaine
            if partner.ref == '1502623':
                to_address = 'eric.delafontaine@aligro.ch'
            self.email_id = self.env['mail.compose.message'].with_context(
                lang=partner.lang).create_emails(
                    template, self.id, {
                        'email_to': to_address,
                        'email_from': from_address
                    })
            # Add message in partner
            self.correspondant_id.write({
                'message_ids': [(4, self.email_id.mail_message_id.id)]})

            # Automatically send letters, except for the first one
            if not self.is_first_letter and self.destination_language_id in \
                    self.supporter_languages_ids and \
                    self.sponsorship_id.state == 'active':
                self.email_id.send_sendgrid()

    def get_image(self, user=None):
        """ Mark the e-mail as read. """
        data = super(SponsorshipCorrespondence, self).get_image(user)
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
