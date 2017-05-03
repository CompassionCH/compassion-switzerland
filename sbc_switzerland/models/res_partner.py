# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emmanuel Mathier <emmanuel.mathier@gmail.com>, Emanuel Cino
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import fields, models


class ResPartner(models.Model):
    """ Add correspondence preferences to Partners
    """
    _inherit = 'res.partner'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    letter_delivery_preference = fields.Selection(
        selection='_get_delivery_preference',
        default='auto_digital',
        required=True,
        help='Delivery preference for Child Letters',
    )
