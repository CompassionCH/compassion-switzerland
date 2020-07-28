##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.http import request, route
from odoo.addons.website_event_compassion.controllers.events_controller import (
    EventsController,
)


class CrowdFundingWebsite(EventsController):
    @route(["/my_account"], type="http", auth="user", website=True)
    def my_account(self, form_id=None, **kw):
        """ Inject data for forms. """
        values = {}
        partner = request.env.user.partner_id
        participations = request.env["crowdfunding.participant"].search(
            [
                ("partner_id", "=", partner.id),
                ("project_id.project_owner_id", "!=", partner.id),
            ]
        )
        donations = participations.mapped("invoice_line_ids").filtered(
            lambda l: l.state == "paid")

        owned_projects = request.env["crowdfunding.project"].search(
            [("project_owner_id", "=", partner.id)]
        )

        kw["form_model_key"] = "cms.form.partner.coordinates"
        coordinates_form = self.get_form("res.partner", partner.id, **kw)
        if form_id is None or form_id == coordinates_form.form_id:
            coordinates_form.form_process()

        values.update(
            {
                "partner": partner,
                "owned_projects": owned_projects,
                "participating_projects": participations,
                "donations": donations,
                "coordinates_form": coordinates_form,
            }
        )

        result = request.render(
            "crowdfunding_compassion.myaccount_crowdfunding_view_template", values
        )
        return result

    @route(["/my_account/project/update/"], type="http", auth="user", website=True)
    def my_account_projects_update(self, project_id=None, **kw):
        project = request.env["crowdfunding.project"].search([("id", "=", project_id)])
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
                "crowdfunding_compassion.crowdfunding_form_template", values
            )
        return result

    @route(
        ["/my_account/participation/update/"], type="http", auth="user", website=True
    )
    def my_account_participants_update(self, participant_id=None, **kw):
        participant = request.env["crowdfunding.participant"].search(
            [("id", "=", participant_id)]
        )
        kw["form_model_key"] = "cms.form.crowdfunding.participant.update"
        participant_update_form = self.get_form(
            "crowdfunding.participant", participant.id, **kw
        )
        participant_update_form.form_process()

        values = {
            "form": participant_update_form,
        }
        if participant_update_form.form_success:
            result = request.redirect("/my_account")
        else:
            result = request.render(
                "crowdfunding_compassion.crowdfunding_form_template", values
            )
        return result
