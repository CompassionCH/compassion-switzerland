import werkzeug

from odoo.http import request, route

from odoo.addons.cms_form.controllers.main import FormControllerMixin
from odoo.addons.cms_form_compassion.controllers.payment_controller import (
    PaymentFormController,
)


class DonationController(PaymentFormController, FormControllerMixin):
    @route(
        ["/project/<model('crowdfunding.project'):project>/donation"],
        auth="public",
        website=True,
        sitemap=False
    )
    def project_donation_page(self, page=1, project=None, **kwargs):
        """ To preselect a participant, pass its id as particpant query parameter """
        if not project.website_published:
            return request.redirect("/projects")
        participant = kwargs.pop("participant", False)
        if int(page) == 1 and len(project.participant_ids) == 1:
            page = 2
            participant = project.participant_ids.id
        if int(page) == 2 and not project.number_sponsorships_goal:
            # Skip directly to donation page
            participant = request.env["crowdfunding.participant"].browse(participant)
            return self.project_donation_form_page(3, project, participant, **kwargs)

        return request.render(
            "crowdfunding_compassion.project_donation_page", {
                "project": project.sudo(),
                "selected_participant": participant,
                "page": page,
                "skip_type_selection": not project.number_sponsorships_goal,
            },
        )

    @route(
        [
            "/project/<model('crowdfunding.project'):project>"
            "/donation/form/<model('crowdfunding.participant'):participant>"
        ],
        auth="public",
        website=True,
        sitemap=False
    )
    def project_donation_form_page(self, page=3, project=None, participant=None, **kwargs):
        if not project.website_published:
            return request.redirect("/projects")
        kwargs["form_model_key"] = "cms.form.crowdfunding.donation"

        donation_form = self.get_form(
            "crowdfunding.participant", participant.id, **kwargs
        )
        donation_form.form_process()

        # If the form is valid, redirect to payment
        if donation_form.form_success:
            return werkzeug.utils.redirect(donation_form.form_next_url(), code=303)

        context = {
            "project": project.sudo(),
            "participant": participant.sudo(),
            "form": donation_form,
            "main_object": participant.sudo(),
            "page": page
        }

        return request.render(
            "crowdfunding_compassion.project_donation_page", context,
        )

    @route(
        "/crowdfunding/payment/validate/<int:invoice_id>", auth="public", website=True,
        sitemap=False
    )
    def crowdfunding_donation_validate(self, invoice_id=None, **kwargs):
        """ Method called after a payment attempt """

        payment = kwargs.get("payment")

        try:
            invoice = request.env["account.invoice"].sudo().browse(int(invoice_id))
            invoice.exists().ensure_one()
            transaction = invoice.get_portal_last_transaction()
        except ValueError:
            transaction = request.env["payment.transaction"]

        if transaction.state != "done" or payment == "error":
            return request.render("crowdfunding_compassion.donation_failure")

        else:
            comm_obj = request.env["partner.communication.job"].sudo()

            # Send confirmation email
            config = request.env.ref(
                "crowdfunding_compassion.config_donation_successful_email_template"
            )
            comm_obj.create({
                "config_id": config.id,
                "partner_id": invoice.partner_id.id,
                "object_ids": invoice.ids
            })

        return request.render("crowdfunding_compassion.donation_successful")
