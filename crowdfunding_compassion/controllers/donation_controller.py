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
        no_sitemap=True
    )
    def project_donation_page(self, project, **kwargs):
        """ To preselect a participant, pass its id as particpant query parameter """
        if not project.website_published:
            return request.redirect("/projects")
        participant = kwargs.get("participant")

        return request.render(
            "crowdfunding_compassion.project_donation_page",
            {"project": project.sudo(), "selected_participant": participant},
        )

    @route(
        [
            "/project/<model('crowdfunding.project'):project>"
            "/donation/form/<model('crowdfunding.participant'):participant>"
        ],
        auth="public",
        website=True,
        no_sitemap=True
    )
    def project_donation_form_page(self, project, participant, **kwargs):
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
        }

        return request.render(
            "crowdfunding_compassion.project_donation_form_page", context,
        )

    @route(
        "/crowdfunding/payment/validate/<int:invoice_id>", auth="public", website=True,
        no_sitemap=True
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
