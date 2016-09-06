# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import models, fields


class MassMailing(models.Model):
    """ Add the mailing domain to be viewed in a text field
    """
    _inherit = 'mail.mass_mailing'

    mailing_domain_copy = fields.Char(related='mailing_domain')
