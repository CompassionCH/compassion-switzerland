#    Copyright (C) 2020 Compassion CH
#    @author: Quentin Gigon

from datetime import date, datetime

from babel.dates import format_timedelta

from odoo import models, api, fields

import urllib.parse as urlparse


class CrowdfundingProject(models.Model):
    _name = "crowdfunding.project"
    _inherit = ["website.published.mixin", "website.seo.metadata", "mail.thread",
                "mail.activity.mixin"]
    _inherits = {'utm.campaign': 'campaign_id'}
    _description = "Crowd-funding project"

    description = fields.Text(
        "Project description",
        help="Aim of the project, why you want to create it, for which purpose and "
             "any useful information that the donors should know.",
        required=True
    )
    type = fields.Selection(
        [("individual", "Individual"), ("collective", "Collective")],
        required=True,
        default="individual",
    )
    deadline = fields.Date(
        "Deadline of project",
        help="Indicate when your project should end.",
        required=True, index=True)
    time_left = fields.Char(compute="_compute_time_left")
    cover_photo = fields.Binary(
        "Cover Photo",
        help="Upload a cover photo that represents your project. Best size: 900x400px",
        attachment=True)
    cover_photo_url = fields.Char(compute="_compute_cover_photo_url")
    presentation_video = fields.Char(
        help="Paste any video link that showcase your project"
             " (e.g. https://vimeo.com/jlkj34ek5)"
    )
    presentation_video_embed = fields.Char(
        compute="_compute_presentation_video_embed"
    )
    facebook_url = fields.Char("Facebook link")
    twitter_url = fields.Char("Twitter link")
    instagram_url = fields.Char("Instagram link")
    personal_web_page_url = fields.Char("Personal web page")
    product_id = fields.Many2one(
        "product.product", "Supported fund",
        domain=[("activate_for_crowdfunding", "=", True)])
    product_number_goal = fields.Integer(compute="_compute_product_number_goal")
    product_number_reached = fields.Integer(compute="_compute_product_number_reached")
    number_sponsorships_goal = fields.Integer(
        compute="_compute_number_sponsorships_goal"
    )
    number_sponsorships_reached = fields.Integer(
        compute="_compute_number_sponsorships_reached"
    )
    sponsorship_ids = fields.Many2many(
        "recurring.contract", string="Sponsorships",
        compute="_compute_sponsorships"
    )
    invoice_line_ids = fields.One2many(
        "account.invoice.line", compute="_compute_invoice_line_ids", string="Donations"
    )
    project_owner_id = fields.Many2one("res.partner", "Project owner", required=True)
    owner_participant_id = fields.Many2one(
        "crowdfunding.participant", compute="_compute_owner_participant_id"
    )
    participant_ids = fields.One2many(
        "crowdfunding.participant", "project_id", string="Participants"
    )
    event_id = fields.Many2one("crm.event.compassion", "Event")
    campaign_id = fields.Many2one('utm.campaign', 'UTM Campaign',
                                  required=True, ondelete='cascade')
    state = fields.Selection(
        [("draft", "Draft"), ("active", "Active")],
        required=True,
        default="draft",
        readonly=True,
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
                "start_date": vals.get("deadline"),
                "end_date": vals.get("deadline"),
                "hold_start_date": date.today(),
                "number_allocate_children": vals.get("product_number_goal"),
                "planned_sponsorships": vals.get("number_sponsorships_goal"),
                "type": "crowdfunding",
            }
        )
        res.event_id = event
        self.env["recurring.contract.origin"].create({
            "type": "crowdfunding",
            "event_id": event.id,
            "analytic_id": event.analytic_id.id,
        })
        res.add_owner2participants()
        return res

    @api.multi
    def add_owner2participants(self):
        """Add the project owner to the participant list. """
        for project in self:
            if project.project_owner_id not in project.participant_ids.mapped(
                    "partner_id"
            ):
                participant = {
                    "partner_id": project.project_owner_id.id,
                    "project_id": project.id,
                }
                project.write({"participant_ids": [(0, 0, participant)]})

    # create an embedded version of the user input of presentation_video
    @api.onchange("presentation_video")
    def _compute_presentation_video_embed(self):
        if self.presentation_video:
            url_data = urlparse.urlparse(self.presentation_video)
            if "youtube" in url_data.hostname and "embed" not in url_data.path:
                query = urlparse.parse_qs(url_data.query)
                self.presentation_video_embed = \
                    "/".join([url_data.scheme + "://" + url_data.hostname, "embed",
                              query["v"][0]])
            elif "vimeo" in url_data.hostname and "video" not in url_data.path:
                self.presentation_video_embed = "/".join([
                    url_data.scheme + "://player." + url_data.hostname, "video",
                    url_data.path.lstrip("/")
                ])
            else:
                self.presentation_video_embed = self.presentation_video

    @api.multi
    def _compute_product_number_goal(self):
        for project in self:
            project.product_number_goal = sum(
                project.participant_ids.mapped('product_number_goal'))

    @api.multi
    def _compute_product_number_reached(self):
        for project in self:
            invl = project.invoice_line_ids.filtered(lambda l: l.state == "paid")
            project.product_number_reached = int(
                sum(invl.mapped("price_total")) / project.product_id.standard_price
            ) if project.product_id.standard_price else 0

    @api.multi
    def _compute_number_sponsorships_goal(self):
        for project in self:
            project.number_sponsorships_goal = sum(
                project.participant_ids.mapped('number_sponsorships_goal'))

    @api.multi
    def _compute_sponsorships(self):
        for project in self:
            project.sponsorship_ids = self.env["recurring.contract"].search([
                ("campaign_id", "=", project.campaign_id.id),
                ("type", "like", "S"),
                ("state", "!=", "cancelled")
            ])

    @api.multi
    def _compute_number_sponsorships_reached(self):
        for project in self:
            project.number_sponsorships_reached = len(project.sponsorship_ids)

    @api.multi
    def _compute_website_url(self):
        for project in self:
            project.website_url = "/projects/create/confirm"

    @api.multi
    def _compute_time_left(self):
        for project in self:
            project.time_left = format_timedelta(
                project.deadline - date.today(), locale=self.env.lang[:2]
            )

    @api.multi
    def _compute_owner_participant_id(self):
        for project in self:
            project.owner_participant_id = project.participant_ids.filtered(
                lambda p: p.partner_id == project.project_owner_id
            ).id

    @api.multi
    def _compute_cover_photo_url(self):
        domain = self.env['website'].get_current_website()._get_http_domain()
        for project in self:
            project.cover_photo_url = \
                f"{domain}/web/content/crowdfunding.project/{project.id}/cover_photo"

    @api.multi
    def _compute_invoice_line_ids(self):
        for project in self:
            project.invoice_line_ids = self.env["account.invoice.line"].search([
                ("crowdfunding_participant_id", "in", project.participant_ids.ids)
            ])

    @api.multi
    def validate(self):
        self.write({"state": "active"})
        comm_obj = self.env["partner.communication.job"]
        config = self.env.ref("crowdfunding_compassion.config_project_published")
        for project in self:
            # Send email to inform project owner
            comm_obj.create(
                {
                    "config_id": config.id,
                    "partner_id": project.project_owner_id.id,
                    "object_ids": project.id,
                }
            )

    @api.model
    def get_active_projects(self, limit=None, year=None, type=None):
        filters = list(filter(None, [
            ("state", "!=", "draft"),
            ("deadline", ">=", datetime(year, 1, 1)) if year else None,
            ("deadline", "<=", datetime(year, 12, 31)) if year else None,
            ("type", "=", type) if type else None
        ]))

        # Get active projects, from most urgent to least urgent
        active_projects = self.search(
            [
                ("deadline", ">=", date.today()),
            ] + filters, limit=limit, order="deadline ASC"
        )

        # Get finished projects, from most recent to oldest expiring date
        finished_projects = self.env[self._name]
        if not limit or (limit and len(active_projects) < limit):
            finish_limit = limit-len(active_projects) if limit else None
            finished_projects = self.search(
                [
                    ("deadline", "<", date.today()),
                ] + filters, limit=finish_limit, order="deadline DESC"
            )

        return active_projects + finished_projects

    def _default_website_meta(self):
        res = super()._default_website_meta()
        res['default_opengraph']['og:description'] = res[
            'default_twitter']['twitter:description'] = self.description
        res['default_opengraph']['og:image'] = res[
            'default_twitter']['twitter:image'] = self.cover_photo_url
        res['default_opengraph']['og:image:secure_url'] = self.cover_photo_url
        res['default_opengraph']['og:image:type'] = "image/jpeg"
        res['default_opengraph']['og:image:width'] = "640"
        res['default_opengraph']['og:image:height'] = "442"
        return res
