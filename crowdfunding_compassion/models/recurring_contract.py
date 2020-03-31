#    Copyright (C) 2020 Compassion CH
#    @author: Quentin Gigon

from odoo import models, fields


class RecurringContract(models.Model):
    _inherit = "recurring.contract"

    crowdfunding_participant_id = fields.Many2one(
        "crowdfunding.participant", "Crowdfunding participant")
    crowdfunding_project_id = fields.Many2one(
        "crowdfunding.project", "Crowdfunding project")
