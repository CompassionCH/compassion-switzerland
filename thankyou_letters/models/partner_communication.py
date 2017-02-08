# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp import api, models


class PartnerCommunication(models.Model):
    _inherit = 'partner.communication.job'

    @api.multi
    def get_success_story(self):
        return "Success Story"
