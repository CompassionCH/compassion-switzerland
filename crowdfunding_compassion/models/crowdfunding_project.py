#    Copyright (C) 2020 Compassion CH
#    @author: Quentin Gigon

from odoo import models, api, fields, _


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
        required=True, default="individual"
    )
    deadline = fields.Date(string="Deadline of project", required=True)
    cover_photo = fields.Binary(string="Cover Photo")
    presentation_video = fields.Char(string="Youtube/Vimeo link")
    facebook_url = fields.Char(string="Facebook link")
    twitter_url = fields.Char(string="Twitter link")
    instagram_url = fields.Char(string="Instagram link")
    personal_web_page_url = fields.Char(string="Personal web page")
    product_id = fields.Many2one("product.product")  # fund
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
    project_owner_id = fields.Many2one("crowdfunding.participant")
    participant_ids = fields.One2many(
        "crowdfunding.participant",
        "partner_id",
        string="Participants")
    event_id = fields.Many2one("event.compassion")
    # doit créer un event lié automatiquement à
    # la création du projet en remplissant le champs:
    #     nom
    #     dates
    #     expected_sponsorships
    #     etc..

    @api.multi
    def _compute_product_number_reached(self):
        return 0

    @api.multi
    def _compute_number_sponsorships_reached(self):
        return 0
