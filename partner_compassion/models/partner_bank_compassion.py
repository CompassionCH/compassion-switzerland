# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Steve Ferry
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, _


class ResPartnerBank(models.Model):
    """ This class upgrade the partners.bank to match Compassion needs.
    """

    _inherit = 'res.partner.bank'

    @api.model
    def create(self, data):
        """Override function to notify creation in a message
        """
        result = super(ResPartnerBank, self).create(data)

        part = result.partner_id
        part.message_post(_("<b>Account number: </b>" + result.acc_number),
                          _("New account created"), _('comment'))

        return result

    @api.multi
    def unlink(self):
        """Override function to notify delte in a message
        """
        for account in self:
            part = account.partner_id
            part.message_post(_("<b>Account number: </b>" +
                                account.acc_number),
                              _("Account deleted"), _('comment'))

        result = super(ResPartnerBank, self).unlink()
        return result
