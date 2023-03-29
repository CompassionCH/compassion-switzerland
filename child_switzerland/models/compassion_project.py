##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields


class CompassionProject(models.Model):
    _inherit = "compassion.project"

    desc_fr = fields.Html("French description", readonly=True)
    desc_de = fields.Html("German description", readonly=True)
    desc_it = fields.Html("Italian description", readonly=True)
