##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    @author: Noé Berdoz <nberdoz@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from base64 import b64decode

from werkzeug.exceptions import NotFound

from odoo import SUPERUSER_ID, _
from odoo.http import Response, content_disposition, request, route

from odoo.addons.my_compassion.controllers.my_account import MyAccountController
from odoo.addons.my_compassion.controllers.website_utils import safe_int


class MyAccountControllerSwitzerland(MyAccountController):
    def _generate_pdf_response(self, wizard):
        """
        Render the PDF of a report wizard and send it as a download.
        :param wizard: a report_compassion print wizard with pdf enabled
        :return: a response to download the generated PDF
        """
        wizard.get_report()
        return Response(
            b64decode(wizard.pdf_download),
            content_type="application/pdf",
            headers=[("Content-Disposition", content_disposition(wizard.pdf_name))],
        )

    @route("/my/download/<source>", type="http", auth="user", website=True)
    def download_file(self, source, **kw):
        """
        Add the Swiss documents to the downloadable sources: the tax receipt of
        a fiscal year, the payment slips of a sponsorship and the payment slips
        for the gifts of a sponsored child.
        :param source: Tells which document we want
        :param kw: the additional optional arguments
        :return: a response to download the file
        """
        partner = request.env.user.partner_id
        if source == "tax_receipt":
            year = safe_int(kw.get("year"), 0)
            if not year:
                raise NotFound()
            wizard = (
                request.env["print.tax_receipt"]
                .with_user(SUPERUSER_ID)
                .with_context(active_ids=partner.ids)
                .create(
                    {
                        "pdf": True,
                        "year": year,
                        "pdf_name": _("tax_receipt") + f"_{year}.pdf",
                    }
                )
            )
            return self._generate_pdf_response(wizard)

        if source == "gift_bvr":
            child_id = safe_int(kw.get("child_id"), -1)
            sponsorship = partner.sponsorship_ids.filtered(
                lambda s: s.state not in ["cancelled", "terminated"]
                and s.child_id.id == child_id
            )[:1]
            if not sponsorship:
                raise NotFound()
            wizard = (
                request.env["print.sponsorship.gift.bvr"]
                .with_user(SUPERUSER_ID)
                .with_context(
                    active_ids=sponsorship.id, active_model="recurring.contract"
                )
                .sudo()
                .create(
                    {
                        "pdf": True,
                        "paper_format": "report_compassion.2bvr_gift_sponsorship",
                    }
                )
            )
            return self._generate_pdf_response(wizard)

        if source == "csp_bvr":
            # Survival sponsorships are left out of sponsorship_ids: they are
            # only added to the three contract fields it is computed from.
            csp_id = safe_int(kw.get("csp_id"), -1)
            sponsorship = (
                partner.contracts_correspondant
                + partner.contracts_paid
                + partner.contracts_fully_managed
            ).filtered(lambda s: s.id == csp_id)
            if not sponsorship:
                raise NotFound()
            wizard = (
                request.env["print.sponsorship.bvr"]
                .with_user(SUPERUSER_ID)
                .with_context(
                    active_ids=sponsorship.id, active_model="recurring.contract"
                )
                .sudo()
                .create(
                    {
                        "pdf": True,
                        "paper_format": "report_compassion.2bvr_sponsorship",
                    }
                )
            )
            return self._generate_pdf_response(wizard)

        return super().download_file(source, **kw)
