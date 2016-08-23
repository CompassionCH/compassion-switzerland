# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Philippe Heer
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp import models, fields


class ResCompany(models.Model):
    _name = "res.company"
    _inherit = "res.company"

    bvr_message_horz = fields.Float(
        'BVR Horz. message Delta (inch)',
        help='horiz. delta in inch 1.2 will print the bvr message 1.2 inch' +
             ' lefter,'
        ' negative value is possible'
    )

    bvr_message_vert = fields.Float(
        'BVR Vert. message Delta (inch)',
        help='vert. delta in inch 1.2 will print the bvr message 1.2 inch' +
             ' lefter,'
        ' negative value is possible'
    )
