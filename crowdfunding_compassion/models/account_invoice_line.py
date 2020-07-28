#    Copyright (C) 2020 Compassion CH
#    @author: Quentin Gigon

from odoo import models, fields, api


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    crowdfunding_participant_id = fields.Many2one(
        "crowdfunding.participant", "Crowdfunding participant"
    )
    is_anonymous = fields.Boolean(default=False)

    @api.onchange("crowdfunding_participant_id")
    def _update_utm_data(self):
        self.source_id = self.crowdfunding_participant_id.source_id.id
        self.campaign_id =  self.crowdfunding_participant_id.project_id.campaign_id.id
