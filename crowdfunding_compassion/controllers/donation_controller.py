from odoo.http import request, route

from odoo.addons.cms_form.controllers.main import FormControllerMixin
from odoo.addons.cms_form_compassion.controllers.payment_controller import (
    PaymentFormController,
)


class ProjectController(PaymentFormController, FormControllerMixin):

    # To preselect a participant, pass its id as particpant query parameter
    @route(
        ["/project/<model('crowdfunding.project'):project>/donation"],
        auth="public",
        website=True,
    )
    def project_donation_page(self, project, **kwargs):
        participant = kwargs.get("participant")

        return request.render(
            "crowdfunding_compassion.project_donation_page",
            {"project": project.sudo(), "selected_participant": participant},
        )

    @route(
        [
            "/project/<model('crowdfunding.project'):project>/donation/form/<model('crowdfunding.participant'):participant>"
        ],
        auth="public",
        website=True,
    )
    def project_donation_form_page(self, project, participant, **kwargs):
        kwargs["form_model_key"] = "cms.form.crowdfunding.donation"

        donation_form = self.get_form(
            "crowdfunding.participant", participant.id, **kwargs)
        donation_form.form_process()

        context = {
            "project": project.sudo(),
            "participant": participant.sudo(),
            "form": donation_form,
            "main_object": participant.sudo(),
        }

        # if donation_form.form_success:
        #     # The user submitted a donation, redirect to confirmation
        #     return werkzeug.utils.redirect(donation_form.form_next_url(), code=303)

        return request.render(
            "crowdfunding_compassion.project_donation_form_page", context,
        )
