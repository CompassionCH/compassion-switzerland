##############################################################################
#
#    Copyright (C) 2021 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields


class FieldOffice(models.Model):
    _inherit = "compassion.field.office"

    alumni_representative = fields.Char()
    alumni_video_link = fields.Char(translate=True)
    alumni_gender = fields.Selection([("M", "Male"), ("F", "Female")])
