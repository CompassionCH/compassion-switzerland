# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017-2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models


class AccountInvoice(models.Model):
    """ Add utm links in invoice objects. """
    _inherit = ['account.invoice', 'utm.mixin']
    _name = 'account.invoice'
