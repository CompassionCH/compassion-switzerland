#    Copyright (C) 2020 Compassion CH
#    @author: Quentin Gigon

from datetime import date

from babel.dates import format_timedelta

from odoo import models, api, fields


class CrowdfundingProject(models.Model):
    _name = "crowdfunding.project"
    _inherit = "website.published.mixin"
    _description = "Crowd-funding project"

    name = fields.Char(required=True)
    description = fields.Text()
    personal_motivation = fields.Text()
    type = fields.Selection(
        [("individual", "Individual"), ("collective", "Collective")],
        required=True,
        default="individual",
    )
    deadline = fields.Date(string="Deadline of project", required=True, index=True)
    time_left = fields.Char(compute="_compute_time_left")
    cover_photo = fields.Binary(string="Cover Photo", attachment=True)
    presentation_video = fields.Char(string="Youtube/Vimeo link")
    facebook_url = fields.Char(string="Facebook link")
    twitter_url = fields.Char(string="Twitter link")
    instagram_url = fields.Char(string="Instagram link")
    personal_web_page_url = fields.Char(string="Personal web page")
    product_id = fields.Many2one("product.product", "Supported fund")
    product_number_goal = fields.Integer(default=1)
    product_number_reached = fields.Integer(compute="_compute_product_number_reached")
    number_sponsorships_goal = fields.Integer(default=1)
    number_sponsorships_reached = fields.Integer(
        compute="_compute_number_sponsorships_reached"
    )
    sponsorship_ids = fields.One2many(
        "recurring.contract", "crowdfunding_project_id", string="Sponsorships"
    )
    invoice_line_ids = fields.One2many(
        "account.invoice.line", "crowdfunding_project_id", string="Donations"
    )
    project_owner_id = fields.Many2one("res.partner", "Project owner", required=True)
    participant_ids = fields.One2many(
        "crowdfunding.participant", "project_id", string="Participants"
    )
    event_id = fields.Many2one("crm.event.compassion", "Event")
    state = fields.Selection(
        [("draft", "Draft"), ("active", "Active")],
        required=True,
        default="draft",
        readonly=True
    )
    owner_lastname = fields.Char(string="Your lastname")
    owner_firstname = fields.Char(string="Your firstname")
    active = fields.Boolean(default=True)

    @api.model
    def create(self, vals):
        res = super().create(vals)
        event = self.env["crm.event.compassion"].create(
            {
                "name": vals.get("name"),
                "event_type_id": self.env.ref(
                    "crowdfunding_compassion.event_type_crowdfunding"
                ).id,
                "crowdfunding_project_id": res.id,
                "company_id": self.env.user.company_id.id,
                "start_date": date.today(),
                "end_date": vals.get("deadline"),
                "hold_start_date": date.today(),
                "number_allocate_children": vals.get("product_number_goal"),
                "planned_sponsorships": vals.get("number_sponsorships_goal"),
                "type": "crowdfunding",
            }
        )
        res.event_id = event
        res.add_owner2participants()
        return res

    @api.multi
    def write(self, vals):
        super().write(vals)
        self.add_owner2participants()
        return True

    @api.multi
    def add_owner2participants(self):
        """Add the project owner to the participant list. """
        for project in self:
            if project.project_owner_id not in project.participant_ids.mapped(
                    'partner_id'):
                participant = {
                    'partner_id': project.project_owner_id.id,
                    'project_id': project.id
                }
                project.write({"participant_ids": [(0, 0, participant)]})

    @api.multi
    def _compute_product_number_reached(self):
        for project in self:
            project.product_number_reached = (
                sum(project.invoice_line_ids.mapped("price_unit"))
                / project.product_id.list_price
            )

    @api.multi
    def _compute_number_sponsorships_reached(self):
        for project in self:
            project.number_sponsorships_reached = len(project.sponsorship_ids)

    def get_active_projects_list(self, number=999):
        projects = self.search([
            ("state", "!=", "draft")
        ], limit=number, order="deadline ASC")

        project_list = list(projects)
        output = []
        # while there are at least 3 projects in the set
        while len(project_list) >= 2:
            row = [project_list.pop(0), project_list.pop(0), project_list.pop(0)]
            output.append(row)

        if len(project_list) > 0:
            output.append(project_list)

        return output

    @api.multi
    def _compute_website_url(self):
        for project in self:
            project.website_url = "/projects/create/confirm"

    @api.multi
    def _compute_time_left(self):
        for project in self:
            project.time_left = format_timedelta(
                project.deadline - date.today(), locale="en"
            )

    @api.multi
    def validate(self):
        for project in self:
            project.state = "active"

            # Send email to inform project owner
            comm_obj = self.env["partner.communication.job"]
            config = self.env.ref("crowdfunding_compassion.config_project_published")
            comm_obj.create(
                {
                    "config_id": config.id,
                    "partner_id": project.project_owner_id,
                    "object_ids": project.id,
                }
            )
