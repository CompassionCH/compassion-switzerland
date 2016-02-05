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

from openerp import models, fields, api, _


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
            if self._partner_needs_explanations(partner.id):
                template_name = self.env.ref(
                    'sbc_email.first_letter_templatename')
            else:
                template_name = self.env.ref(
                    'sbc_email.new_letter_templatename')

            template = self.env['sponsorship.templatelist'].search([
                ('name_id', '=', template_name.id),
                ('lang', '=', partner.lang)])
            child = self.child_id.firstname
            # Create and send email
            self.email_id = self.env['mail.mail'].create({
                'email_to': partner.email,
                'layout_template_id': template.layout_template_id.id,
                'text_template_id': template.text_template_id.id,
                'substitution_ids': [
                    (0, _, {'key': 'child', 'value': child}),
                    (0, _, {'key': 'letter_url', 'value': self.read_url}),
                    (0, _, {'key': 'intro', 'value': template.intro or ''}),
                    (0, _, {'key': 'tweet', 'value': template.tweet or ''}),
                ],
                'model': 'res.partner',
                'res_id': self.correspondant_id.id,
            })
            # Automatically send letters, except for the first one
            if not self.is_first_letter:
                self.email_id.send_sendgrid()

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _partner_needs_explanations(self, partner_id):
        """ Returns true if the partner never received explanations
            about the new correspondence system. The partner should have a
            sponsorship that began before the transition of system.
        """
        self.ensure_one()
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
