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
        donations = []
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
            donations = participant.invoice_line_ids

        kw["form_model_key"] = "cms.form.partner.coordinates"
        coordinates_form = self.get_form("res.partner", partner.id, **kw)
        if form_id is None or form_id == coordinates_form.form_id:
            coordinates_form.form_process()
            form_success = coordinates_form.form_success

        values.update({
            "partner": partner,
            "owned_projects": owned_projects,
            "participating_projects": participating_projects,
            "donations": donations,
            "coordinates_form": coordinates_form,
        })

        result = request.render(
            "crowdfunding_compassion.myaccount_crowdfunding_view_template", values)
        return result

    @route(["/my_account/project/edit/"], type="http", auth="user", website=True)
    def my_account_projects_edit(self, project_id=None, **kw):
        project = request.env['crowdfunding.project'].search([
            ('id', '=', project_id)
        ])
        kw["form_model_key"] = "cms.form.crowdfunding.project.update"
        project_update_form = self.get_form("crowdfunding.project", project.id, **kw)
        project_update_form.form_process()

        values = {
            "form": project_update_form,
        }
        if project_update_form.form_success:
            result = request.redirect("/my_account")
        else:
            result = request.render(
                "crowdfunding_compassion.project_update_view_template", values)
        return result
