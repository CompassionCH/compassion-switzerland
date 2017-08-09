# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from odoo import models, fields


class EventCompassion(models.Model):
    _inherit = 'crm.event.compassion'

    thank_you_text = fields.Html(translate=True)
