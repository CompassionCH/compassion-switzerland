##############################################################################
#
#    Copyright (C) 2021 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import fields, models


class FieldOffice(models.Model):
    _inherit = ["compassion.field.office", "translatable.model"]
    _name = "compassion.field.office"

    alumni_representative = fields.Char()
    alumni_video_link = fields.Char(translate=True)
    alumni_gender = fields.Selection([("M", "Male"), ("F", "Female")])

    # TPL 2026 fields
    director_gender = fields.Selection([("M", "Male"), ("F", "Female")])
    tpl_prayer = fields.Char("Prayer", translate=True)
    tpl_praise = fields.Char("Praise", translate=True)
    tpl_looking_forward = fields.Char("Looking forward", translate=True)
    tpl_nb_fcps_with_intervention = fields.Integer("FCPs with intervention")
    tpl_nb_years_partnership = fields.Integer("Years partnership")
    tpl_nb_participants = fields.Integer("Participants")
