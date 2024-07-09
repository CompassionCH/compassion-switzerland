##############################################################################
#
#    Copyright (C) 2024 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Noé Berdoz <nberdoz@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import http
from odoo.http import request
from werkzeug.exceptions import NotFound
import base64


class EmployeeImageController(http.Controller):
    @http.route(
        '/employee/image/<int:employee_id>/',
        auth='public',
        type='http',
        methods=["GET"],
        website=True,
        sitemap=False
    )
    def get_employee_image(self, employee_id):
        """
        Retrieves the image for a given employee ID and returns it as a PNG image.

        Args:
            employee_id (int): The unique identifier of the employee whose image is requested.

        Returns:
            werkzeug.wrappers.Response: A response object containing the binary image data,

        Raises:
            werkzeug.exceptions.NotFound
        """
        employee = request.env['hr.employee'].sudo().browse(employee_id)
        if not employee.image_128:
            raise NotFound()

        # Decode the base64 image as binary image
        image_data = base64.b64decode(employee.image_128)

        # Return the binary image directly in the browser
        return request.make_response(
            image_data,
            headers=[
                ('Content-Type', 'image/png'),
                ('Content-Disposition', 'inline; filename="employee_image.png"'),
            ]
        )
