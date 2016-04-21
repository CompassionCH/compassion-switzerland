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
        english = self.env.ref('sbc_compassion.lang_compassion_english')
        for contract in self:
            if contract.reading_language != english:
                contract.sudo(contract.create_uid)._send_ticket()
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
            template = self.env.ref('sbc_email.ticket_change_language')
            change_text = '{},{},{}<br/>'.format(
                contract.partner_codega,
                contract.child_code,
                contract.reading_language.name)
            # Find outgoing email
            email_obj = self.env['mail.mail']
            email = email_obj.search([
                ('subject', '=', template.subject),
                ('state', '=', 'outgoing')])
            if not email:
                # Create email
                email = self.env['mail.compose.message'].create_emails(
                    template, contract.id, {
                        'email_to': TICKET_TO,
                        'email_from': TICKET_FROM,
                        'email_cc': TICKET_CC,
                        'substitution_ids': [
                            (0, False, {'key': '{changes}', 'value': ''}),
                        ]
                    })
            content = email.substitution_ids[0]
            content.value = content.value + change_text
