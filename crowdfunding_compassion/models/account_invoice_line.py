#    Copyright (C) 2020 Compassion CH
#    @author: Quentin Gigon

from odoo import models, fields, api


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"
    state = fields.Selection(index=True)
    campaign_id = fields.Many2one("utm.campaign", index=True)
    crowdfunding_participant_id = fields.Many2one(
        "crowdfunding.participant", "Crowdfunding participant",
        domain=[("project_id.state", "=", "active"),
                ("project_id.active", "=", True),
                ("project_id.deadline", ">=", fields.Date.today())],
        index=True
    )
    is_anonymous = fields.Boolean(default=False)

    @api.onchange("crowdfunding_participant_id")
    def _update_utm_data(self):
        if self.crowdfunding_participant_id:
            self.source_id = self.crowdfunding_participant_id.source_id
            self.campaign_id =\
                self.crowdfunding_participant_id.project_id.campaign_id
            self.medium_id = self.env.ref(
                "crowdfunding_compassion.utm_medium_crowdfunding")
            self.account_analytic_id = \
                self.crowdfunding_participant_id.project_id.event_id.analytic_id

    @api.multi
    def _get_ambassador_receipt_config(self):
        """
        Check if donation is linked to a crowdfunding event.
        :return: partner.communication.config record
        """
        # ambassador = self.mapped("user_id")
        crowdfunding_event = self.mapped("event_id.crowdfunding_project_id")
        if crowdfunding_event:
            return self.env.ref(
                "crowdfunding_compassion.config_donation_received"
            )
        return super()._get_ambassador_receipt_config()
