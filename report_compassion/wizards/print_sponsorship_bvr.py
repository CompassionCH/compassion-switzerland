##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PrintSponsorshipBvr(models.TransientModel):
    """
    Wizard for selecting a period and the format for printing
    payment slips of a sponsorship.
    """

    _name = "print.sponsorship.bvr"
    _description = (
        "Select a period and the format " "for printing payment slips of a sponsorship"
    )

    def _compute_default_period_selection(self):
        # After december 15th choose next year by default, to avoid blank BVRs
        today = date.today()
        return "next_year" if today >= date(today.year, 12, 15) else "this_year"

    period_selection = fields.Selection(
        [
            ("this_year", "Current year"),
            ("next_year", "Next year"),
        ],
        default=_compute_default_period_selection,
    )
    paper_format = fields.Selection(
        [
            ("report_compassion.2bvr_sponsorship", "2 BVR"),
            ("report_compassion.bvr_sponsorship", "Single BVR A4"),
            ("report_compassion.single_bvr_sponsorship", "Single BVR"),
        ],
        default="report_compassion.2bvr_sponsorship",
    )
    date_start = fields.Date(default=lambda s: s.default_start())
    date_stop = fields.Date(default=lambda s: s.default_stop())
    include_gifts = fields.Boolean()
    state = fields.Selection([("new", "new"), ("pdf", "pdf")], default="new")
    pdf = fields.Boolean()
    pdf_name = fields.Char(default="sponsorship payment.pdf")
    pdf_download = fields.Binary(readonly=True)

    @api.model
    def default_start(self):
        today = date.today()
        start = today.replace(day=1, month=1)
        # Exception in December, we want to print for next year.
        if today.month == 12 and today.day >= 15:
            start = start.replace(year=today.year + 1)
        return start.replace(day=1)

    @api.model
    def default_stop(self):
        today = date.today()
        stop = today.replace(day=31, month=12)
        # Exception in December, we want to print for next year.
        if today.month == 12 and today.day >= 15:
            stop = stop.replace(year=today.year + 1)
        return stop

    @api.onchange("period_selection")
    def onchange_period(self):
        today = date.today()
        start = self.date_start
        stop = self.date_stop
        if self.period_selection == "this_year":
            start = start.replace(year=today.year)
            stop = stop.replace(year=today.year)
        elif self.period_selection == "next_year":
            start = start.replace(year=today.year + 1)
            stop = stop.replace(year=today.year + 1)
        self.date_start = start
        self.date_stop = stop

    def get_report(self):
        """
        Prepare data for the report and call the selected report
        (single bvr / 2 bvr).
        :return: Generated report
        """
        if self.date_start >= self.date_stop:
            raise UserError(_("Date stop must be after date start."))
        data = {
            "date_start": self.date_start,
            "date_stop": self.date_stop,
            "gifts": self.include_gifts,
            "doc_ids": self.env.context.get("active_ids"),
        }
        report_name = "report_compassion.report_" + self.paper_format.split(".")[1]
        report_ref = self.env.ref(report_name)
        if self.pdf:
            pdf_data = report_ref.with_context(
                must_skip_send_to_printer=True
            )._render_qweb_pdf(data["doc_ids"], data=data)[0]
            self.pdf_download = base64.encodebytes(pdf_data)
            self.state = "pdf"
            return {
                "name": "Download report",
                "type": "ir.actions.act_window",
                "res_model": self._name,
                "res_id": self.id,
                "view_mode": "form",
                "target": "new",
                "context": self.env.context,
            }
        return report_ref.report_action(data["doc_ids"], data=data, config=False)


class PrintBvrDue(models.TransientModel):
    """
    Wizard for selecting a period and the format for printing
    payment slips of a sponsorship.
    """

    _name = "print.sponsorship.bvr.due"
    _description = "Print sponsorship due BVR"

    state = fields.Selection([("new", "new"), ("pdf", "pdf")], default="new")
    pdf = fields.Boolean()
    pdf_name = fields.Char(default="sponsorship due.pdf")
    pdf_download = fields.Binary(readonly=True)

    def get_report(self):
        """
        Prepare data for the report
        :return: Generated report
        """
        records = self.env[self.env.context.get("active_model")].browse(
            self.env.context.get("active_ids")
        )
        data = {
            "doc_ids": records.ids,
        }
        report_ref = self.env.ref("report_compassion.report_bvr_due")
        if self.pdf:
            pdf_data = report_ref.with_context(
                must_skip_send_to_printer=True
            )._render_qweb_pdf(records.ids, data=data)[0]
            self.pdf_download = base64.encodebytes(pdf_data)
            self.state = "pdf"
            return {
                "name": "Download report",
                "type": "ir.actions.act_window",
                "res_model": self._name,
                "res_id": self.id,
                "view_mode": "form",
                "target": "new",
                "context": self.env.context,
            }
        return report_ref.report_action(data["doc_ids"], data=data, config=False)
