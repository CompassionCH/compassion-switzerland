# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Coninckx <david@coninckx.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields


class CompassionChild(models.Model):
    _inherit = 'compassion.child'

    desc_fr = fields.Text('French description', readonly=True)
    desc_de = fields.Text('German description', readonly=True)
    desc_it = fields.Text('Italian description', readonly=True)
