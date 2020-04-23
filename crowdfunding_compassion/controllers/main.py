##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo.http import request, route, Controller
from odoo.addons.website_event_compassion.controllers.events_controller import (
    EventsController,
)


class CrowdFundingWebsite(EventsController):

    @route(["/my_account"], type="http", auth="user", website=True)
    def my_account(self, form_id=None, **kw):
        """ Inject data for forms. """
        values = {}
        participating_projects = []
        owned_projects = []
        partner = request.env.user.partner_id
        participant = request.env['crowdfunding.participant'].search([
            ('partner_id', '=', partner.id)
        ])
        if participant:
            participating_projects = request.env['crowdfunding.project'].search([
                ('participant_ids', 'in', participant.id)
            ])
            owned_projects = request.env['crowdfunding.project'].search([
                ('project_owner_id', '=', participant.id),
            ])

        kw["form_model_key"] = "cms.form.partner.coordinates"
        coordinates_form = self.get_form("res.partner", partner.id, **kw)
        if form_id is None or form_id == coordinates_form.form_id:
            coordinates_form.form_process()
            form_success = coordinates_form.form_success

        values.update({
            "partner": partner,
            "owned_projects": owned_projects,
            "participating_projects": participating_projects,
            "coordinates_form": coordinates_form
        })

        if "registrations" not in values.keys():
            registrations_array = []
            for reg in partner.registration_ids:
                registrations_array.append(reg)
            values['registrations'] = registrations_array

        result = request.render(
            "crowdfunding_compassion.myaccount_crowdfunding_view_template", values)
        return result
