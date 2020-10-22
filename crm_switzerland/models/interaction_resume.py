#    Copyright (C) 2019 Compassion CH
#    @author: Stephane Eicher <seicher@compassion.ch>


from odoo import models, fields


class InteractionResume(models.TransientModel):
    _inherit = "interaction.resume"

    tracking_error_description = fields.Text(
        related="email_id.failure_reason"
    )
