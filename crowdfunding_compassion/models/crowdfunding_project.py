#    Copyright (C) 2020 Compassion CH
#    @author: Quentin Gigon

from odoo import models, api, fields
import datetime


class CrowdfundingProject(models.Model):
    _name = "crowdfunding.project"
    _inherit = "website"
    _description = "Crowd-funding project"

    name = fields.Char(required=True)
    description = fields.Text()
    type = fields.Selection(
        [
            ("individual", "Individual"),
            ("collective", "Collective"),
        ],
        required=True, default="individual"
    )
    deadline = fields.Date(string="Deadline of project", required=True, index=True)
    cover_photo = fields.Binary(string="Cover Photo", attachment=True)
    presentation_video = fields.Char(string="Youtube/Vimeo link")
    facebook_url = fields.Char(string="Facebook link")
    twitter_url = fields.Char(string="Twitter link")
    instagram_url = fields.Char(string="Instagram link")
    personal_web_page_url = fields.Char(string="Personal web page")
    product_id = fields.Many2one("product.product", "Supported fund")
    product_number_goal = fields.Integer()
    product_number_reached = fields.Integer(compute="_compute_product_number_reached")
    number_sponsorships_goal = fields.Integer()
    number_sponsorships_reached = fields.Integer(
        compute="_compute_number_sponsorships_reached")
    sponsorship_ids = fields.One2many(
        "recurring.contract",
        "crowdfunding_project_id",
        string="Sponsorships")
    invoice_line_ids = fields.One2many(
        "account.invoice.line",
        "crowdfunding_project_id",
        string="Donations")
    project_owner_id = fields.Many2one(
        "crowdfunding.participant", "Project owner", required=True, index=True)
    participant_ids = fields.One2many(
        "crowdfunding.participant",
        "project_id",
        string="Participants")
    event_id = fields.Many2one("crm.event.compassion", "Event")
    state = fields.Selection(
        [("validation", "Validation"), ("active", "Active")],
        required=True,
        default="validation",
    )
    # event_type_id = fields.Many2one("event.type", "Event type")

    # TODO fix event.type NULL error
    # @api.model
    # def create(self, vals):
    #     res = super().create(vals)
    #     res.event_id = self.env['crm.event.compassion'].create({
    #         'name': vals.get('name'),
    #         'event_type_id': self.env.ref(
    #             "crowdfunding_compassion.event_type_crowdfunding").id,
    #         'company_id': self.env.user.company_id.id,
    #         'start_date': datetime.date.today(),
    #         'end_date': vals.get('deadline'),
    #         'hold_start_date': datetime.date.today(),
    #         'number_allocate_children': vals.get('product_number_goal'),
    #         'planned_sponsorships': vals.get('number_sponsorships_goal'),
    #         'type': "crowdfunding"
    #     })
    #     return res

    @api.multi
    def _compute_product_number_reached(self):
        for project in self:
            project.product_number_reached = \
                sum(project.invoice_line_ids.mapped('quantity'))

    @api.multi
    def _compute_number_sponsorships_reached(self):
        for project in self:
            project.number_sponsorships_reached = len(project.sponsorship_ids)

    def _get_3_active_projects(self):
        return self.env['crowdfunding.project'].search([
            ("state", "!=", "validation")
        ], limit=3, order="deadline ASC")
