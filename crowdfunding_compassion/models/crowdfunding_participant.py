#    Copyright (C) 2020 Compassion CH
#    @author: Quentin Gigon

from odoo import models, api, fields


class CrowdfundingParticipant(models.Model):
    _name = "crowdfunding.participant"
    _description = "Participant to one of our crowd-fundings"

    project_id = fields.Many2one("crowdfunding.project")
    partner_id = fields.Many2one("res.partner")
    personal_motivation = fields.Text("Personal Motivation")
    product_number_goal = fields.Integer()
    product_number_reached = fields.Integer(compute="_compute_product_number_reached")
    number_sponsorships_goal = fields.Integer()
    number_sponsorships_reached = fields.Integer(compute="_compute_number_sponsorships_reached")
    sponsorship_ids = fields.One2many("recurring.contract", "sponsorships")
    invoice_line_ids = fields.One2many("account.invoice.line", "donations")
    presentation_video = fields.Char("Youtube/Vimeo link")
    facebook_url = fields.Char()
    twitter_url = fields.Char()
    instagram_url = fields.Char()
    personal_web_page_url = fields.Char()
    profile_photo = fields.Binary()
