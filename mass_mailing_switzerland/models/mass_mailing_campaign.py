##############################################################################
#
#    Copyright (C) 2016-2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields

from odoo.addons.queue_job.job import job, related_action


class MassMailingCampaign(models.Model):
    _inherit = "mail.mass_mailing.campaign"
    _order = "id desc"

    contract_ids = fields.One2many(
        "recurring.contract", related="campaign_id.contract_ids"
    )
    correspondence_ids = fields.One2many(
        "correspondence", related="campaign_id.correspondence_ids"
    )
    invoice_line_ids = fields.One2many(
        "account.invoice.line", compute="_compute_campaign_invoices"
    )
    medium_id = fields.Many2one(default=lambda s: s.env.ref(
        'recurring_contract.utm_medium_mass_mailing').id)

    @api.multi
    def _compute_campaign_invoices(self):
        mass_medium = self.env.ref("recurring_contract.utm_medium_mass_mailing")
        for campaign in self:
            campaign.invoice_line_ids = campaign.campaign_id.invoice_line_ids.filtered(
                lambda invl: invl.medium_id == mass_medium
            )


class Mail(models.Model):
    _inherit = "mail.mail"

    @job(default_channel="root.mass_mailing")
    @related_action(action="related_action_emails")
    @api.multi
    def send_sendgrid_job(self, mass_mailing_ids=False):
        # Make send method callable in a job
        self.send_sendgrid()
        if mass_mailing_ids:
            mass_mailings = self.env["mail.mass_mailing"].browse(mass_mailing_ids)
            mass_mailings.write({"state": "done"})
        return True
