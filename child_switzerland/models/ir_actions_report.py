##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def print_document(self, record_ids, data=None):
        # The childpack wizard lets the user pick the paper tray. The chosen
        # tray travels in ``data`` (like the language) because the printing
        # client action of base_report_to_printer only forwards the report
        # action's ``data`` to the server.
        tray = (data or {}).get("input_tray")
        if tray:
            self = self.with_context(childpack_input_tray=tray)
        return super().print_document(record_ids, data=data)

    def behaviour(self):
        result = super().behaviour()
        tray = self.env.context.get("childpack_input_tray")
        if tray:
            result["input_tray"] = tray
        return result
