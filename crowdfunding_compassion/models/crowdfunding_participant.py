#    Copyright (C) 2020 Compassion CH
#    @author: Quentin Gigon

from odoo import models, api, fields


class CrowdfundingParticipant(models.Model):
    _name = "crowdfunding.participant"
    _description = "Participant to one of our crowd-fundings"

    project_id = fields.Many2one("crowdfunding.project", string="Partner project")
    partner_id = fields.Many2one("res.partner", string="Partner")
    personal_motivation = fields.Text(string="Personal Motivation")
    product_number_goal = fields.Integer()
    product_number_reached = fields.Integer(compute="_compute_product_number_reached")
    number_sponsorships_goal = fields.Integer()
    number_sponsorships_reached = fields.Integer(
        compute="_compute_number_sponsorships_reached")
    # TODO fix one2many fields
    sponsorship_ids = fields.One2many(
        "recurring.contract",
        "group_id",
        string="Sponsorships")
    invoice_line_ids = fields.One2many(
        "account.invoice.line",
        "contract_id",
        string="Donations")
    presentation_video = fields.Char(help="Youtube/Vimeo link")
    facebook_url = fields.Char(string="Facebook link")
    twitter_url = fields.Char(string="Twitter link")
    instagram_url = fields.Char(string="Instagram link")
    personal_web_page_url = fields.Char(string="Personal web page")
    profile_photo = fields.Binary(string="Profile photo")

    @api.multi
    def _compute_product_number_reached(self):
        return 0

    @api.multi
    def _compute_number_sponsorships_reached(self):
        return 0
