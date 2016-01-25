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

    email_id = fields.Many2one('sendgrid.email')
    email_sent_date = fields.Datetime(related='email_id.sent_date')

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################

    @api.one
    def process_letter(self):
        super(SponsorshipCorrespondence, self).process_letter()
        template = self.env['sponsorship.templatelist'].search(
            [('lang', '=', self.correspondant_id.lang)]
        )
        sponsor = '{} {}'.format(self.correspondant_id.firstname,
                                 self.correspondant_id.lastname)
        child = self.child_id.firstname
        email_to = self.correspondant_id.email
        if email_to:
            # Create and send email
            self.email_id = self.env['sendgrid.email'].create({
                'email_to': email_to,
                'layout_template_id': template.layout_template_id.id,
                'text_template_id': template.text_template_id.id,
                'substitution_ids': [
                    (0, _, {'key': 'sponsor', 'value': sponsor}),
                    (0, _, {'key': 'child', 'value': child}),
                    (0, _, {'key': 'letter_url', 'value': self.read_url}),
                ],
            })
            self.email_id.send()
