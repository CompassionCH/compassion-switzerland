##############################################################################
#
#    Copyright (C) 2023 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    image = fields.Image(
        compute="_compute_image", compute_sudo=True, max_width=128, max_height=128
    )

    def _compute_image(self):
        for line in self:
            line.image = (
                line.product_id.image_128
                or line.registration_id.profile_picture
                or line.participant_id.profile_photo
            )
