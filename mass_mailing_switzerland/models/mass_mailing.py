##############################################################################
#
#    Copyright (C) 2016-2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields, _
from odoo.exceptions import UserError


class MassMailing(models.Model):
    _inherit = "mail.mass_mailing"

    internal_name = fields.Char("Internal Variant Name")

    partner_test_sendgrid_id = fields.Many2one(
        "res.partner", "Test Partner", readonly=False
    )

    # Default values
    mailing_model_id = fields.Many2one(default=lambda s: s.env.ref(
        'base.model_res_partner').id)
    enable_unsubscribe = fields.Boolean(default=True)
    unsubscribe_tag = fields.Char(default="[unsub]")
    mailchimp_country_filter = fields.Char(
        compute="_compute_has_mailchimp_filter")

    @api.multi
    def _compute_has_mailchimp_filter(self):
        country_name = False
        country_filter_id = self.env["res.config.settings"].get_param(
            "mass_mailing_country_filter_id")
        if country_filter_id:
            country_name = self.env[
                "compassion.field.office"].browse(country_filter_id).name
        for mailing in self:
            mailing.mailchimp_country_filter = country_name

    @api.multi
    def name_get(self):
        res = []
        for mass_mail in self:
            _id, _name = super(MassMailing, mass_mail).name_get()[0]
            if mass_mail.internal_name:
                res.append((_id, f"{_name} [{mass_mail.internal_name}]"))
            else:
                res.append((_id, _name))
        return res

    @api.onchange('mailing_model_id', 'contact_list_ids')
    def _onchange_model_and_list(self):
        if self.mailing_model_name == 'res.partner':
            mailing_domain = repr([
                ('customer', '=', True),
                ('opt_out', '=', False),
                ('email', '!=', False)
            ])
        else:
            mailing_domain = super()._onchange_model_and_list()
        self.mailing_domain = mailing_domain

    @api.depends("email_template_id", "partner_test_sendgrid_id")
    def _compute_sendgrid_view(self):
        # change all substitutions if the test partner is set
        for wizard in self:
            res_id = wizard.partner_test_sendgrid_id.id
            template = wizard.email_template_id.with_context(
                lang=wizard.partner_test_sendgrid_id.lang or self.env.context["lang"]
            )
            sendgrid_template = template.sendgrid_localized_template
            if sendgrid_template and res_id:
                render_body = template._render_template(
                    template.body_html, template.model, [res_id], post_process=True
                )[res_id]
                body_sendgrid = sendgrid_template.html_content.replace(
                    "<%body%>", render_body
                )
                substitutions = template.render_substitutions(res_id)
                for sub in substitutions[res_id]:
                    key = sub[2]["key"]
                    value = sub[2]["value"]
                    res_value = template._render_template(
                        value, template.model, [res_id]
                    )[res_id]
                    body_sendgrid = body_sendgrid.replace(key, res_value)
                wizard.body_sendgrid = body_sendgrid
            else:
                super(MassMailing, wizard)._compute_sendgrid_view()

    @api.onchange("partner_test_sendgrid_id")
    def compute_sendgrid_view_test(self):
        self.with_context(
            {"lang": self.lang.code or self.partner_test_sendgrid_id.lang}
        )._compute_sendgrid_view()

    @api.multi
    def send_mail(self):
        # Refresh the sendgrid templates in Odoo
        if self.filtered("email_template_id"):
            self.env["sendgrid.template"].update_templates()
            self.mapped("email_template_id").update_substitutions()

        # Prepare Sendgrid keywords for replacing all urls found
        # in Sendgrid template with tracked URL from Odoo
        emails = self.env["mail.mail"]
        mass_mailing_medium_id = self.env.ref(
            "recurring_contract.utm_medium_mass_mailing"
        ).id
        for mailing in self.with_context(must_skip_send_to_printer=True):
            substitutions = mailing.mapped("email_template_id.substitution_ids")
            substitutions.replace_tracking_link(
                campaign_id=mailing.mass_mailing_campaign_id.campaign_id.id,
                medium_id=mass_mailing_medium_id,
                source_id=mailing.source_id.id,
            )
            emails += super(MassMailing, mailing).send_mail()

        emails_list = []
        final_state = "sending"
        duplicate_emails = self.env["mail.mail"]

        for email in emails:
            # Only update mass mailing state when last e-mail is sent
            mass_mailing_ids = False
            if email == emails[-1]:
                mass_mailing_ids = self.ids

            recipients = [email.email_to] if email.email_to else []
            recipients.extend(email.recipient_ids.mapped("email"))
            if not all(recipient in emails_list for recipient in recipients):
                emails_list.extend(recipients)
                # Used for Sendgrid -> Send e-mails in a job
                email.with_delay().send_sendgrid_job(mass_mailing_ids)
            else:
                # Remove the e-mail, as the recipients already received it.
                statistics = self.env["mail.mail.statistics"].search(
                    [("mail_mail_id", "=", email.id)]
                )
                statistics.unlink()
                duplicate_emails += email
                if email == emails[-1]:
                    # Force the final state to done as it won't be updated by
                    # sending jobs
                    final_state = "done"

        duplicate_emails.unlink()
        self.write({"state": final_state})
        return emails - duplicate_emails

    @api.multi
    def send_pending(self):
        """ Tries to send e-mails still pending. """
        self.ensure_one()
        mail_statistics = self.statistics_ids.filtered(
            lambda s: not s.mail_tracking_id and s.mail_mail_id.state == "outgoing"
        )
        emails = mail_statistics.mapped("mail_mail_id")
        emails.with_delay().send_sendgrid_job(self.ids)
        return True

    @api.model
    def _process_mass_mailing_queue(self):
        """
        Override cron to take only "in_queue" mass mailings.
        Pending mass_mailings may be still processing.
        :return: None
        """
        mass_mailings = self.search(
            [
                ("state", "=", "in_queue"),
                "|",
                ("schedule_date", "<", fields.Datetime.now()),
                ("schedule_date", "=", False),
            ]
        )
        for mass_mailing in mass_mailings:
            if len(mass_mailing.get_remaining_recipients()) > 0:
                mass_mailing.state = "sending"
                mass_mailing.send_mail()
            else:
                mass_mailing.state = "done"

    def send_now_mailchimp(self, account=False):
        queue_job = self.env["queue.job"].search([
            ("channel", "=", "root.mass_mailing_switzerland.update_mailchimp"),
            ("state", "!=", "done")
        ], limit=1)
        if queue_job:
            raise UserError(_(
                "Mailchimp is updating its MERGE FIELDS right now. "
                "You should wait for the process to finish before sending the mailing."
            ))
        return super().send_now_mailchimp(account)
