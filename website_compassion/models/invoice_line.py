##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    @author: Théo Nikles <theo.nikles@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields


class AccountInvoiceLine(models.Model):
    _name = "account.invoice.line"
    _inherit = ["account.invoice.line", "translatable.model"]


class AccountInvoice(models.Model):
    _inherit = "account.invoice"
    # If true, cancel the invoice if the linked payment transaction is cancelled
    cancel_invoice = fields.Boolean(default=False)
