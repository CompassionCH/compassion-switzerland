#    Copyright (C) 2020 Compassion CH
#    @author: Quentin Gigon

from odoo import models, api, fields


class CrowdfundingParticipant(models.Model):
    _name = "crowdfunding.participant"
    _description = "Participant to one of our crowd-fundings"
    _inherit = ["website.seo.metadata", "website.published.multi.mixin", "mail.thread"]
    _inherits = {'utm.source': 'source_id'}

    project_id = fields.Many2one(
        "crowdfunding.project",
        index=True, ondelete="cascade", string="Project", required=True)
    partner_id = fields.Many2one(
        "res.partner", string="Partner", required=True, index=True, ondelete="cascade"
    )
    personal_motivation = fields.Text()
    product_number_goal = fields.Integer(default=0)
    product_number_reached = fields.Integer(compute="_compute_product_number_reached")
    number_sponsorships_goal = fields.Integer(default=0)
    number_sponsorships_reached = fields.Integer(
        compute="_compute_number_sponsorships_reached"
    )
    sponsorship_ids = fields.Many2many(
        "recurring.contract", compute="_compute_sponsorships", string="Sponsorships"
    )
    invoice_line_ids = fields.One2many(
        "account.invoice.line", "crowdfunding_participant_id", string="Donations"
    )
    source_id = fields.Many2one('utm.source', 'UTM Source',
                                required=True, ondelete='cascade')
    presentation_video = fields.Char(
        help="Paste any video link that showcase your project"
             " (e.g. https://vimeo.com/jlkj34ek5)")
    facebook_url = fields.Char(string="Facebook link")
    twitter_url = fields.Char(string="Twitter link")
    instagram_url = fields.Char(string="Instagram link")
    personal_web_page_url = fields.Char(string="Personal web page")
    profile_photo = fields.Binary(related="partner_id.image")
    profile_photo_url = fields.Char(compute="_compute_profile_photo_url")
    sponsorship_url = fields.Char(compute="_compute_sponsorship_url")

    _sql_constraints = [
        ('registration_unique', "unique(project_id,partner_id)",
         "Only one registration per participant/project is allowed!")
    ]

    @api.model
    def create(self, vals):
        partner = self.env["res.partner"].browse(vals.get("partner_id"))
        project = self.env["crowdfunding.project"].browse(vals.get("project_id"))
        vals["name"] = f"{project.name} - {partner.name}"
        return super().create(vals)

    @api.model
    def get_sponsorship_url(self, participant_id):
        return self.browse(participant_id).sudo().sponsorship_url

    @api.multi
    def _compute_sponsorship_url(self):
        wp = self.env["wordpress.configuration"].sudo().get_config()
        for participant in self:
            utm_medium = "Crowdfunding"
            utm_campaign = participant.project_id.name
            utm_source = participant.name
            participant.sponsorship_url = \
                f"https://{wp.host}{wp.sponsorship_url}?" \
                f"utm_medium={utm_medium}" \
                f"&utm_campaign={utm_campaign}" \
                f"&utm_source={utm_source}"

    @api.multi
    def _compute_product_number_reached(self):
        for participant in self:
            invl = participant.invoice_line_ids.filtered(lambda l: l.state == "paid")
            participant.product_number_reached = int(sum(invl.mapped("quantity")))

    @api.multi
    def _compute_sponsorships(self):
        for participant in self:
            participant.sponsorship_ids = self.env["recurring.contract"].search([
                ("source_id", "=", participant.source_id.id),
                ("type", "like", "S"),
                ("state", "!=", "cancelled")
            ])

    @api.multi
    def _compute_number_sponsorships_reached(self):
        for participant in self:
            participant.number_sponsorships_reached = len(participant.sponsorship_ids)

    @api.multi
    def _compute_profile_photo_url(self):
        domain = self.env['website'].get_current_website()._get_http_domain()
        for participant in self:
            title = participant.sudo().partner_id.title.with_context(lang="en_US")
            if participant.profile_photo:
                path = f"web/content/crowdfunding.participant" \
                    f"/{participant.id}/profile_photo"
            elif title.name == "Mister":
                path = "crowdfunding_compassion/static/src/img/guy.png"
            elif title.name == "Madam":
                path = "crowdfunding_compassion/static/src/img/lady.png"
            else:
                path = None

            participant.profile_photo_url = f"{domain}/{path}" if path else path
