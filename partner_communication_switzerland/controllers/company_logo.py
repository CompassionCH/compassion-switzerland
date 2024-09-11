##############################################################################
#
#    Copyright (C) 2024 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nicolas Praz <npraz@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64

from werkzeug.exceptions import NotFound

from odoo import http
from odoo.http import request


class CompanyLogoController(http.Controller):
    @http.route("/company/logo/<int:company_id>/", auth="public")
    def get_company_logo(self, company_id):
        """
        Retrieves the company logo for a given ID and returns it as a PNG image.

        Args:
            company_id (int)

        Returns:
            werkzeug.wrappers.Response: A response object with the binary image data

        Raises:
            werkzeug.exceptions.NotFound
        """
        company = request.env["res.company"].sudo().browse(company_id)
        if not company.logo_web:
            raise NotFound()

        # Decode the base64 image as binary image
        image_data = base64.b64decode(company.logo_web)

        # Return the binary image directly as response
        return request.make_response(
            image_data,
            headers=[
                ("Content-Type", "image/png"),
                ("Content-Disposition", 'inline; filename="company_logo.png"'),
            ],
        )