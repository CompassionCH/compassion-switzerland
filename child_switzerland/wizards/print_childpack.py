##############################################################################
#
#    Copyright (C) 2016-2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, fields, models


class PrintChildpack(models.TransientModel):
    """
    Wizard for selecting a the child dossier type and language.
    """

    _inherit = "print.childpack"

    # Trays holding the pre-printed forms of the full childpack, by language
    # prefix. Other languages and childpack types use the Paper Source
    # configured on the report.
    FULL_TRAY_BY_LANG_PREFIX = {
        "de": "Cassette 3",
        "fr": "Cassette 4",
    }

    type = fields.Selection(
        selection_add=[("child_switzerland.childpack_mini", "Mini Childpack")]
    )
    printer_id = fields.Many2one(
        "printing.printer", compute="_compute_printer_tray", store=True
    )
    printer_tray_id = fields.Many2one(
        "printing.tray.input",
        "Paper Source",
        compute="_compute_printer_tray",
        store=True,
        readonly=False,
        domain="[('printer_id', '=', printer_id)]",
    )

    def _compute_module_name(self):
        res = super()._compute_module_name()
        if self.type == "child_switzerland.childpack_mini":
            self.module_name = __name__.split(".")[2]
        return res

    def _get_childpack_report(self):
        """Return the ir.actions.report of the selected childpack type."""
        self.ensure_one()
        module, template = self.type.split(".")
        return self.env.ref(f"{module}.report_{template}", raise_if_not_found=False)

    @api.depends("type", "lang")
    def _compute_printer_tray(self):
        for wizard in self:
            report = wizard.type and wizard._get_childpack_report()
            if not report:
                wizard.printer_id = False
                wizard.printer_tray_id = False
                continue
            printer = (
                report.printing_printer_id
                or self.env.user.printing_printer_id
                or self.env["printing.printer"].get_default()
            )
            tray = report.printer_input_tray_id
            if wizard.type == "child_compassion.childpack_full" and wizard.lang:
                tray_name = self.FULL_TRAY_BY_LANG_PREFIX.get(wizard.lang[:2])
                if tray_name:
                    tray = (
                        self.env["printing.tray.input"].search(
                            [
                                ("printer_id", "=", printer.id),
                                ("name", "=ilike", tray_name),
                            ],
                            limit=1,
                        )
                        or tray
                    )
            wizard.printer_id = printer
            wizard.printer_tray_id = tray if tray.printer_id == printer else False

    def get_report(self):
        res = super().get_report()
        if (
            not self.pdf
            and self.printer_tray_id
            and res.get("type") == "ir.actions.report"
        ):
            # Forward the chosen tray to the printing client action, which
            # only carries the report action's ``data`` back to the server
            # (see ir.actions.report.print_document).
            data = res.get("data") or {}
            data["input_tray"] = self.printer_tray_id.system_name
            res["data"] = data
        return res
