#    Copyright (C) 2020 Compassion CH
#    @author: Quentin Gigon

from odoo import models, api, fields


class CrowdfundingProject(models.Model):
    _name = "crowdfunding.project"
    _inherit = "website"
    _description = "Crowd-funding project"

    name = fields.Char()
    description = fields.Text()
    type = fields.Selection(
        [
            ("individual", _("Individual")),
            ("collective", _("Collective")),
        ],
        required=True
    )
    deadline = fields.Date()
    cover_photo = fields.Binary()
    presentation_video = fields.Char(help="Youtube or Vimeo link")
    facebook_url = fields.Char()
    twitter_url = fields.Char()
    instagram_url = fields.Char()
    personal_web_page_url = fields.Char()
    product_id = fields.Many2one("product.product") # fund
    product_number_goal = fields.Integer()
    product_number_reached = fields.Integer(compute="_compute_product_number_reached")
    number_sponsorships_goal = fields.Integer()
    number_sponsorships_reached = fields.Integer(compute="_compute_number_sponsorships_reached")
    sponsorship_ids = fields.One2many("recurring.contract", "sponsorships")
    invoice_line_ids = fields.One2many("account.invoice.line", "donations")
    project_owner_id = fields.Many2one("crowdfunding.participant")
    participant_ids = fields.One2many("crowdfunding.participant")
    event_id = fields.Many2one("event.compassion"),
    # doit créer un event lié automatiquement à la création du projet en remplissant le champs:
    #     nom
    #     dates
    #     expected_sponsorships
    #     etc..

