#    Copyright (C) 2020 Compassion CH
#    @author: Quentin Gigon

from odoo import models, api, fields


class CrowdfundingParticipant(models.Model):
    _name = "crowdfunding.participant"
    _description = "Participant to one of our crowd-fundings"
    _inherit = ["website.seo.metadata", "website.published.multi.mixin"]

    name = fields.Char(related="partner_id.name", readonly=True)
    project_id = fields.Many2one(
        "crowdfunding.project",
        index=True, ondelete="cascade", string="Project", required=True)
    partner_id = fields.Many2one(
        "res.partner", string="Partner", required=True, index=True, ondelete="cascade"
    )
    personal_motivation = fields.Text()
    product_number_goal = fields.Integer(default=1)
    product_number_reached = fields.Integer(compute="_compute_product_number_reached")
    number_sponsorships_goal = fields.Integer(default=1)
    number_sponsorships_reached = fields.Integer(
        compute="_compute_number_sponsorships_reached"
    )
    sponsorship_ids = fields.One2many(
        "recurring.contract", "crowdfunding_participant_id", string="Sponsorships"
    )
    invoice_line_ids = fields.One2many(
        "account.invoice.line", "crowdfunding_participant_id", string="Donations"
    )
    presentation_video = fields.Char(help="Youtube/Vimeo link")
    facebook_url = fields.Char(string="Facebook link")
    twitter_url = fields.Char(string="Twitter link")
    instagram_url = fields.Char(string="Instagram link")
    personal_web_page_url = fields.Char(string="Personal web page")
    profile_photo = fields.Binary(string="Profile photo")
    sponsorship_url = fields.Char(compute="_compute_sponsorship_url")

    @api.model
    def create(self, vals):
        res = super().create(vals)
        self.env['utm.source'].create({
            'name': res.partner_id.name
        })
        return res

    @api.model
    def get_sponsorship_url(self, participant_id):
        participant = self.env['crowdfunding.participant'].sudo().search([
            ('id', '=', participant_id)
        ])
        return participant.sponsorship_url

    @api.multi
    def _compute_sponsorship_url(self):
        for participant in self:
            utm_medium = "Crowdfunding"
            utm_campaign = participant.project_id.name
            utm_source = participant.partner_id.name
            participant.sponsorship_url = f"https://compassion.ch/parrainer-un-enfant/?" \
                                          f"utm_medium={utm_medium}" \
                                          f"&utm_campaign={utm_campaign}" \
                                          f"&utm_source={utm_source}"

    @api.multi
    def _compute_product_number_reached(self):
        for participant in self:
            participant.product_number_reached = (
                sum(participant.invoice_line_ids.mapped("price_unit"))
                / participant.project_id.product_id.list_price
            )

    @api.multi
    def _compute_number_sponsorships_reached(self):
        for participant in self:
            participant.number_sponsorships_reached = len(participant.sponsorship_ids)
