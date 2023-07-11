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


# pylint: disable=C8107
class ResPartnerBank(models.Model):
    """This class upgrade the partners.bank to match Compassion needs."""

    _inherit = "res.partner.bank"

    def _get_partner_address_lines(self, partner):
        """Override to allow empty zip or city."""
        line_1 = (
            (partner and partner.street or "")
            + " "
            + (partner and partner.street2 or "")
        )
        line_2 = (
            (partner and partner.zip or "") + " "
            + (partner and partner.city or "")
        )
        return line_1[:70], line_2[:70]

    @api.model_create_multi
    def create(self, data):
        """Override function to notify creation in a message"""
        result = super().create(data)
        for bank in result:
            if bank.partner_id:
                bank.message_post(
                    body=_("<b>Account number: </b>" + bank.acc_number),
                    subject=_("New account created"),
                    type="comment",
                )
        return result

    def unlink(self):
        """Override function to notify delete in a message"""
        for account in self:
            part = account.partner_id
            part.message_post(
                body=_("<b>Account number: </b>" + account.acc_number),
                subject=_("Account deleted"),
                type="comment",
            )

        result = super().unlink()
        return result
