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

    email_id = fields.Many2one(
        'mail.mail', 'E-mail', related='communication_id.email_id',
        store=True)
    communication_id = fields.Many2one(
        'partner.communication.job', 'Communication')
    sent_date = fields.Datetime(
        'Communication sent', related='communication_id.sent_date',
        oldname='email_sent_date', store=True)
    email_read = fields.Boolean(compute='_compute_email_read', store=True)

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
        if partner.email and partner.letter_delivery_preference == 'digital' \
            and not\
                self.email_id:
            if self.partner_needs_explanations():
                template = self.env.ref('sbc_email.change_system')
            else:
                template = self.env.ref('sbc_email.new_letter')

            # EXCEPTION FOR DEMAUREX : send to Delafontaine
            email = None
            auto_send = self._can_auto_send() and composed_ok
            if partner.ref == '1502623':
                email = 'eric.delafontaine@aligro.ch'
            communication_type = self.env.ref('sbc_email.child_letter_config')
            self.communication_id = self.env[
                'partner.communication.job'].create({
                    'config_id': communication_type.id,
                    'partner_id': partner.id,
                    'object_id': self.id,
                    'auto_send': auto_send,
                    'email_template_id': template.id,
                    'email_to': email,
                })

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
            # Check that the translation is filled
            valid = self.page_ids.filtered('translated_text') and \
                self.translation_language_id in partner_langs
        return valid
