
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


MANDATE_STATE = {'create': 'created',
                 'cancel': 'cancelled',
                 'validate': 'validated',
                 'back2draft': 'back to draft',
                 'delete': 'deleted'}


# pylint: disable=C8107
class AccountBankingMandate(models.Model):
    """ This class upgrade the partners.bank to match Compassion needs.
    """
    _inherit = 'account.banking.mandate'

    def _update_mandate_status_partner(self, action):
        """
        Post a message on the partner's message feed with the new state
        of the mandate
        """
        self.ensure_one()

        if action in MANDATE_STATE:
            self.partner_id.message_post(
                _("For account: " + (self.partner_bank_id.acc_number or '')),
                _("Mandate " + MANDATE_STATE[action]), 'comment')

    @api.model
    def create(self, data):
        """Override function to notify creation in a message on partner feed
        """
        result = super().create(data)
        result._update_mandate_status_partner('create')

        return result

    @api.multi
    def validate(self):
        """
        Override function to notify validation in a message on partner feed
        """

        for mandate in self:
            mandate._update_mandate_status_partner('validate')

        super().validate()

        return True

    @api.multi
    def cancel(self):
        """
        Override function to notify cancellation in a message on partner feed
        """

        for mandate in self:
            mandate._update_mandate_status_partner('cancel')

        super().cancel()
        return True

    @api.multi
    def back2draft(self):
        """
        Override function to notify cancellation in a message on partner feed
        """

        for mandate in self:
            mandate._update_mandate_status_partner('back2draft')

        super().back2draft()
        return True

    @api.multi
    def unlink(self):
        """
        Override function to notify removal in a message on partner feed
        """

        for mandate in self:
            mandate._update_mandate_status_partner('delete')

        result = super().unlink()
        return result
