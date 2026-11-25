##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import fields, models


class CompassionIntervention(models.Model):
    _inherit = "compassion.intervention"

    church_presentation_text = fields.Html(
        translate=True,
        help="Presentation of the project director and of the community center, "
        "used in the communications sent to the churches.",
    )
    project_director_photo = fields.Image(
        max_width=600,
        max_height=800,
        help="Photo of the project director, used in the communications. "
        "Stored in the filestore and kept small, as it is sent by e-mail.",
    )
