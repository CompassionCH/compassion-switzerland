from base64 import b64decode
from datetime import datetime

from werkzeug.datastructures import Headers
from werkzeug.wrappers import Response

from odoo import SUPERUSER_ID, _
from odoo.http import request, route

from odoo.addons.my_compassion.controllers.my_account import MyAccountController


class MyPortal(MyAccountController):
    def _prepare_portal_layout_values(self):
        """Add custom values to the portal layout."""
        values = super()._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        create_date = (
            request.env["account.move"]
            .sudo()
            .search(
                [
                    ("partner_id", "=", partner.id),
                    ("payment_state", "=", "paid"),
                    ("move_type", "=", "out_invoice"),
                    ("amount_total", ">", 0),
                ],
                limit=1,
                order="create_date asc",
            )
            .create_date
        )

        current_year = datetime.today().year
        first_year = create_date.year if create_date else current_year
        values.update(
            {
                "current_year": current_year,
                "first_year": first_year,
            }
        )
        return values

    @route("/my/download/<source>", type="http", auth="user", website=True)
    def download_file(self, source, **kw):
        partner = request.env.user.partner_id
        if source == "tax_receipt":
            year = kw["year"]
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
            wizard.get_report()
            headers = Headers()
            headers.add("Content-Disposition", "attachment", filename=wizard.pdf_name)
            data = b64decode(wizard.pdf_download)
            return Response(data, content_type="application/pdf", headers=headers)
        if source == "gift_bvr":
            child_id = int(kw["child_id"])

            sponsorship = partner.sponsorship_ids.filtered(
                lambda s: s.state not in ["cancelled", "terminated"]
                and s.child_id.id == child_id
            )

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
            wizard.get_report()
            headers = Headers()
            headers.add("Content-Disposition", "attachment", filename=wizard.pdf_name)
            data = b64decode(wizard.pdf_download)
            return Response(data, content_type="application/pdf", headers=headers)

        return super().download_file(source, **kw)
