##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from functools import reduce

from odoo import models

_logger = logging.getLogger(__name__)


class CompassionChild(models.Model):
    """Add fields for retrieving values for communications.
    Send a communication when a major revision is received.
    """

    _inherit = "compassion.child"

    def get_completion(self):
        """Return the full completion dates."""
        month = self[0].completion_month
        year = self[0].completion_date.strftime("%Y")
        if not month:
            return year
        return month + " " + year

    def get_hold_gifts(self):
        """
        :return: True if all children's gift are held.
        """
        return reduce(lambda x, y: x and y, self.mapped("project_id.hold_gifts"))
