##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import fields, api
from odoo.addons.base_geoengine import geo_model


class MuskathlonDetails(geo_model.GeoModel):
    _inherit = "advocate.details"

    trip_information_complete = fields.Boolean(
        compute='_compute_trip_information_complete'
    )

    @api.multi
    def _compute_trip_information_complete(self):
        for record in self:
            registration = record.partner_id.registration_ids[:1]
            trip_info = [
                registration.emergency_name, registration.emergency_phone,
                registration.emergency_relation_type,
                registration.t_shirt_size, registration.passport_number,
                registration.passport_expiration_date, registration.birth_name
            ]
            for info in trip_info:
                if not info:
                    record.trip_information_complete = False
                    break
            else:
                record.trip_information_complete = True
