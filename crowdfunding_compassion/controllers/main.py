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
    @route(["/my/together"], type="http", auth="user", website=True,
           sitemap=False)
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
        donations = request.env["account.invoice.line"].sudo().search(
            [
                ("crowdfunding_participant_id.partner_id", "=", partner.id),
                ("state", "=", "paid"),
            ]
        )

        owned_projects = request.env["crowdfunding.project"].search(
            [("project_owner_id", "=", partner.id)]
        )

        values.update(
            {
                "partner": partner,
                "owned_projects": owned_projects,
                "participating_projects": participations,
                "donations": donations,
            }
        )

        result = request.render(
            "crowdfunding_compassion.my_account_crowdfunding_view_template", values
        )
        return result

    @route(["/my/together/project/update/"], type="http", auth="user", website=True,
           sitemap=False)
    def my_account_projects_update(self, project_id=None, **kw):
        project = request.env["crowdfunding.project"].search([("id", "=", project_id)])
        kw["form_model_key"] = "cms.form.crowdfunding.project.update"
        project_update_form = self.get_form("crowdfunding.project", project.id, **kw)
        project_update_form.form_process()

        values = {
            "form": project_update_form,
        }
        if project_update_form.form_success:
            result = request.redirect("/my/together")
        else:
            result = request.render(
                "crowdfunding_compassion.crowdfunding_form_template", values
            )
        return result

    @route(
        ["/my/together/participation/update/"], type="http", auth="user", website=True,
        sitemap=False
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
            result = request.redirect("/my/together")
        else:
            result = request.render(
                "crowdfunding_compassion.crowdfunding_form_template", values
            )
        return result
