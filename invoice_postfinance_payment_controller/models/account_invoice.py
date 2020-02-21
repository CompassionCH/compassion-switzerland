##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    accept_url = fields.Char(
        help="Stores the redirection where the partner should go after the "
        "transaction is completed."
    )
    decline_url = fields.Char(
        help="Stores the redirection where the partner should go after the "
        "transaction is cancelled."
    )
