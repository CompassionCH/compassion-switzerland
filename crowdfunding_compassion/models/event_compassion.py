##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Quentin Gigon
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields


class EventCompassion(models.Model):
    """A Compassion event. """

    _inherit = "crm.event.compassion"

    type = fields.Selection(selection_add=[("crowdfunding", "Crowdfunding")])
