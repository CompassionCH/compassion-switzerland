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

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################

    @api.one
    def send_email(self):
        super(SponsorshipCorrespondence, self).send_email()
        template = self.env['sponsorship.templatelist'].search(
            [('lang', '=', self.correspondant_id.lang)]
        )

        sponsor = '{} {}'.format(self.correspondant_id.firstname,
                                 self.correspondant_id.lastname)
        child = self.child_id.firstname
        self.email_id = self.env['sendgrid.email'].create({
            'email_to': self.correspondant_id.email,
            'layout_template_id': template.layout_template_id.id,
            'text_template_id': template.text_template_id.id,
            'substitution_ids': [
                (0, _, {'key': 'sponsor', 'value': sponsor}),
                (0, _, {'key': 'child', 'value': child}),
                (0, _, {'key': 'letter_url', 'value': self.read_url}),
            ],
        })
        self.email_id.send()
