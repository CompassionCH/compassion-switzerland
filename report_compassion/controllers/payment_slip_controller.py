##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
import logging

from werkzeug.datastructures import Headers
from werkzeug.exceptions import BadRequest, NotFound
from werkzeug.wrappers import Response

from odoo import http
from odoo.http import request, Controller

from odoo.addons.sponsorship_compassion.models.product_names import GIFT_REF

_logger = logging.getLogger(__name__)


class PaymentSlipController(Controller):
    @http.route(
        ["/payment_slip/<string:partner_uuid>/<int:fund_id>",
         "/payment_slip/<string:partner_uuid>/<int:fund_id>/<int:sponsorship_id>"],
        type="http", auth="public", methods=["GET"])
    def get_payment_slip(self, partner_uuid, fund_id, sponsorship_id=None,
                         fund_amount=0):
        """
        URL for getting a payment slip in PDF.
        :param partner_uuid: uuid of the partner.
        :param fund_id: the internal fund_id we use in product.
        :param sponsorship_id: optional sponsorship_id.
        :param fund_amount: optional amount for donation.
        :return: file data for user
        """
        partner = request.env["res.partner"].sudo().search([
            ("uuid", "=", partner_uuid)
        ], limit=1)
        if not partner:
            raise NotFound()
        product = request.env["product.product"].sudo().search([
            ("fund_id", "=", fund_id)
        ], limit=1)
        if not fund_id or not product:
            raise NotFound()
        categ_obj = request.env["product.category"].sudo()
        if not sponsorship_id:
            fund = categ_obj.env.ref("sponsorship_compassion.product_category_fund")
            if product.categ_id != fund:
                raise BadRequest()
            wizard = request.env["print.bvr.fund"].sudo().create({
                "product_id": product.id,
                "draw_background": True,
                "pdf": True,
                "amount": fund_amount
            }).with_context(active_ids=partner.ids)
        else:
            sponsorship = categ_obj.env.ref(
                "sponsorship_compassion.product_category_sponsorship")
            gift = categ_obj.env.ref("sponsorship_compassion.product_category_gift")
            if product.categ_id == sponsorship:
                wizard = request.env["print.sponsorship.bvr"].sudo().create({
                    "paper_format": "report_compassion.bvr_sponsorship",
                    "draw_background": True,
                    "pdf": True
                }).with_context(active_ids=sponsorship_id,
                                active_model="recurring.contract")
            elif product.categ_id == gift:
                try:
                    gift_index = GIFT_REF.index(product.default_code)
                    wizard_vals = {
                        "birthday_gift": gift_index == 0,
                        "general_gift": gift_index == 1,
                        "family_gift": gift_index == 2,
                        "project_gift": gift_index == 3,
                        "graduation_gift": gift_index == 4,
                        "paper_format": "report_compassion.bvr_gift_sponsorship",
                        "draw_background": True,
                        "pdf": True
                    }
                    wizard = request.env["print.sponsorship.gift.bvr"].sudo().create(
                        wizard_vals
                    ).with_context(active_ids=sponsorship_id,
                                   active_model="recurring.contract")
                except ValueError:
                    raise BadRequest()
            else:
                raise BadRequest()
        wizard.get_report()
        headers = Headers()
        headers.add(
            "Content-Disposition", "attachment", filename=wizard.pdf_name
        )
        data = base64.b64decode(wizard.pdf_download)
        return Response(data, content_type="application/pdf", headers=headers)
