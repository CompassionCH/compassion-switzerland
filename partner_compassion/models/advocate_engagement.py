
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields


class AmbassadorEngagement(models.Model):
    _name = "advocate.engagement"
    _description = "Advocate Engagement"

    name = fields.Char(required=True, translate=True)
