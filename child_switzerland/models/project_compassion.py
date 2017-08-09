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


class CompassionProject(models.Model):
    _inherit = 'compassion.project'

    description_fr = fields.Text('French description', readonly=True)
    description_de = fields.Text('German description', readonly=True)
    description_it = fields.Text('Italian description', readonly=True)
