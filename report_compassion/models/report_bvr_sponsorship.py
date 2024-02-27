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

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import Warning as odooWarning

logger = logging.getLogger(__name__)


class BvrSponsorship(models.AbstractModel):
    """
    Model used for preparing data for the bvr report. It can either
    generate 3bvr report, 2bvr report or single bvr report.
    """

    _name = "report.report_compassion.bvr_sponsorship"
    _description = "QR sponsorship report"

    def _get_report(self):
        return self.env["ir.actions.report"]._get_report_from_name(
            "report_compassion.bvr_sponsorship"
        )

    def _get_default_data(self):
        """
        If no data is given for the report, use default values.
        :return: default mandatory data for the bvr report.
        """
        print_bvr_obj = self.env["print.sponsorship.bvr"]
        return {
            "date_start": print_bvr_obj.default_start(),
            "date_stop": print_bvr_obj.default_stop(),
        }

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self._get_report()
        final_data = self._get_default_data()
        if data:
            if data.get("date_start") and isinstance(data["date_start"], str):
                data["date_start"] = fields.Date.from_string(data["date_start"])
            if data.get("date_stop") and isinstance(data["date_stop"], str):
                data["date_stop"] = fields.Date.from_string(data["date_stop"])
            final_data.update(data)
            if not docids and data["doc_ids"]:
                docids = data["doc_ids"]

        start = final_data["date_start"]
        stop = final_data["date_stop"]

        # Months will contain all months we want to include for payment.
        months = list()
        while start <= stop:
            months.append(start)
            start = start + relativedelta(months=1)

        sponsorships = self.env["recurring.contract"].browse(docids)
        sponsorships = sponsorships.filtered(
            lambda s: s.state not in ("terminated", "cancelled")
        )
        groups = sponsorships.mapped("group_id")
        if not groups or not months:
            raise odooWarning(_("Selection not valid. No active sponsorship found."))

        # Docs will contain the groups for which we have to print the payment
        # slip : {'recurring.contract.group': 'recurring.contract' recordset}
        docs = dict()
        for group in groups:
            docs[group] = sponsorships.filtered(lambda s, g=group: s.group_id == g)
        final_data.update(
            {
                "doc_model": report.model,  # recurring.contract.group
                "doc_ids": groups.ids,
                "docs": docs,
                "months": months,
            }
        )
        return final_data


# pylint: disable=consider-merging-classes-inherited
class TwoBvrSponsorship(models.AbstractModel):
    _inherit = "report.report_compassion.bvr_sponsorship"
    _name = "report.report_compassion.2bvr_sponsorship"
    _description = "2QR sponsorship report"

    def _get_report(self):
        return self.env["ir.actions.report"]._get_report_from_name(
            "report_compassion.2bvr_sponsorship"
        )


class BvrSponsorshipDue(models.AbstractModel):
    """
    Allows to send custom data to report.
    """

    _name = "report.report_compassion.bvr_due"
    _description = "QR Sponsorship due report"

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        :param data: data collected from the print wizard.
        :return: html rendered report
        """
        if not data:
            data = {"doc_ids": docids}
        lang = data.get("lang", self.env.lang)
        data.update(
            {
                "doc_model": "recurring.contract",
                "docs": self.env["recurring.contract"]
                .with_context(lang=lang)
                .browse(docids),
            }
        )
        return data


class SingleBvrSponsorship(models.AbstractModel):
    _name = "report.report_compassion.single_bvr_sponsorship"
    _inherit = "report.report_compassion.bvr_sponsorship"
    _description = "Single QR sponsorship report"

    @api.model
    def _get_report_values(self, docids, data=None):
        if data is None:
            raise Exception()
        return super()._get_report_values(docids, data)
