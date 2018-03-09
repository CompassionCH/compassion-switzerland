# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Sebastien Toth <popod@me.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields, api


class PartnerCommunicationSwitzerlandConfig(models.Model):
    _inherit = "partner.communication.config"

    omr_enable_marks = fields.Boolean(string="Enable OMR",
        help="If set to True, the OMR marks are displayed in the "
        "communication."
    )
    omr_should_close_envelope = fields.Boolean(string="OMR should close the "
        "envelope", help="If set to True, the OMR mark for closing the "
        "envelope is added to the communication."
    )
    display_pp = fields.Boolean(string="Display PP",
        help="If not set, the PP is not printed upper the address."
    )
