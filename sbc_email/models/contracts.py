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

from openerp import models, api
from .partner_compassion import TICKET_FROM, TICKET_TO, TICKET_CC


class RecurringContract(models.Model):
    """ Send tickets when correspondence language of sponsorship is changed.
    """
    _inherit = 'recurring.contract'

    @api.multi
    def contract_active(self):
        """ By default, GMC registers new sponsorships with German language.
        Send a ticket if language is not German.
        """
        res = super(RecurringContract, self).contract_active()
        german = self.env.ref('sbc_compassion.lang_compassion_german')
        for contract in self:
            if contract.reading_language != german:
                contract._send_ticket()
        return res

    @api.multi
    def write(self, vals):
        """Send ticket if reading language is changed. """
        res = super(RecurringContract, self).write(vals)
        if 'reading_language' in vals:
            self.filtered(lambda c: c.state == 'active')._send_ticket()
        return res

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _send_ticket(self):
        """ Send ticket to GMC for changing sponsorship language.
        """
        for contract in self:
            text_template = self.env.ref('sbc_email.ticket_change_language')
            # Create and send email
            self.env['mail.mail'].create({
                'email_to': TICKET_TO,
                'email_from': TICKET_FROM,
                'cc_address': TICKET_CC,
                'text_template_id': text_template.id,
                'substitution_ids': [
                    (0, False, {'key': 'supporter',
                                'value': contract.partner_codega}),
                    (0, False, {'key': 'child',
                                'value': contract.child_code}),
                    (0, False, {'key': 'language',
                                'value': contract.reading_language.name}),
                ],
            }).send_sendgrid()
