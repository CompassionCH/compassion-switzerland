##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models

class LinkTracker(models.Model):
    _inherit = 'link.tracker'


    def get_base_url(self):
        return self.env["ir.config_parameter"].sudo().get_param("web.external.url")

