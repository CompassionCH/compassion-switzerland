##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging

from odoo import models

logger = logging.getLogger(__name__)


class ReportChildpackMini(models.AbstractModel):
    _inherit = "report.child_compassion.childpack_full"
    _name = "report.child_switzerland.childpack_mini"
    _description = "Used to generate mini childpack in selected language"

    def _get_report(self):
        return self.env["ir.actions.report"]._get_report_from_name("childpack_mini")
