#    Copyright (C) 2020 Compassion CH
#    @author: Quentin Gigon

from odoo import models, api, fields


class CrowdfundingParticipant(models.Model):
    _name = "crowdfunding.participant"
    _description = "Participant to one of our crowd-fundings"

    name = fields.Char(related="partner_id.name", readonly=True)
    project_id = fields.Many2one(
        "crowdfunding.project",
        index=True, ondelete="cascade", string="Project", required=True)
    partner_id = fields.Many2one(
        "res.partner", string="Partner",
        required=True, index=True, ondelete="cascade")
    personal_motivation = fields.Text()
    product_number_goal = fields.Integer(default=1)
    product_number_reached = fields.Integer(
        compute="_compute_product_number_reached")
    number_sponsorships_goal = fields.Integer(default=1)
    number_sponsorships_reached = fields.Integer(
        compute="_compute_number_sponsorships_reached")
    sponsorship_ids = fields.One2many(
        "recurring.contract",
        "crowdfunding_participant_id",
        string="Sponsorships")
    invoice_line_ids = fields.One2many(
        "account.invoice.line",
        "crowdfunding_participant_id",
        string="Donations")
    presentation_video = fields.Char(help="Youtube/Vimeo link")
    facebook_url = fields.Char(string="Facebook link")
    twitter_url = fields.Char(string="Twitter link")
    instagram_url = fields.Char(string="Instagram link")
    personal_web_page_url = fields.Char(string="Personal web page")
    profile_photo = fields.Binary(string="Profile photo")

    @api.multi
    def _compute_product_number_reached(self):
        for participant in self:
            participant.product_number_reached = \
                sum(participant.invoice_line_ids.mapped('quantity'))

    @api.multi
    def _compute_number_sponsorships_reached(self):
        for participant in self:
            participant.number_sponsorships_reached = len(participant.sponsorship_ids)
