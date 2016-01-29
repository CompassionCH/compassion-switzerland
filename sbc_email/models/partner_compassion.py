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

from openerp import models, api

TICKET_FROM = 'ecino@compassion.com'
TICKET_TO = 'compassion@service-now.com'
TICKET_CC = 'YBoska@us.ci.org'


class ResPartner(models.Model):
    """ Send tickets to GMC in case of change of 'send_original'
    parameter
    """
    _inherit = 'res.partner'

    @api.model
    def create(self, vals):
        partner = super(ResPartner, self).create(vals)
        if partner.send_original:
            partner._send_ticket()
        return partner

    @api.multi
    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        if 'send_original' in vals:
            self._send_ticket()
        return res

    def _send_ticket(self):
        """ Send ticket to GMC to request or cancel sending original
        letters of child. """
        for partner in self:
            if partner.send_original:
                text_template = self.env.ref('sbc_email.ticket_send_original')
            else:
                text_template = self.env.ref(
                    'sbc_email.ticket_block_original')
            # Create and send email
            self.env['mail.mail'].create({
                'email_to': TICKET_TO,
                'email_from': TICKET_FROM,
                'cc_address': TICKET_CC,
                'text_template_id': text_template.id,
                'substitution_ids': [
                    (0, False, {'key': 'supporter', 'value': partner.ref}),
                ],
            }).send_sendgrid()
