#    Copyright (C) 2019 Compassion CH
#    @author: Stephane Eicher <seicher@compassion.ch>


from odoo import models, fields


class InteractionResume(models.TransientModel):
    _inherit = "interaction.resume"

    tracking_error_type = fields.Char(related="email_id.tracking_event_ids.error_type")
    tracking_error_description = fields.Char(
        related="email_id.tracking_event_ids.error_description"
    )
    tracking_error_details = fields.Text(
        related="email_id.tracking_event_ids.error_details"
    )
