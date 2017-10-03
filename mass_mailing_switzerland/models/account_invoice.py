# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from odoo import models, fields


class AccountInvoice(models.Model):
    """ Add mailing origin in invoice objects. """
    _inherit = 'account.invoice'

    mailing_campaign_id = fields.Many2one('mail.mass_mailing.campaign')
