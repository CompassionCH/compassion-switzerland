##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields, _
from odoo.exceptions import UserError


class GenerateWPLink(models.TransientModel):
    _name = "res.partner.generate.wp.link.wizard"
    _description = "Generate Wordpress Link Wizard"

    partner_id = fields.Many2one("res.partner")
    base_url = fields.Char(required=True)
    sponsorship_id = fields.Many2one(
        "recurring.contract", "Filter child")
    donation_type = fields.Selection([
        ("Fund", "Fund donation"),
        ("Sponsor gifts", "Sponsorship gift")
    ])
    product_id = fields.Many2one(
        "product.product", "Preselect donation")
    donation_amount = fields.Float()
    country_filter = fields.Char(compute="_compute_country_filter_active")
    website_link = fields.Char(readonly=True)
    utm_source = fields.Many2one(
        "utm.source", "Tracking source",
        help="If the person makes a donation / writes a letter or make a sponsorship "
             "using this link, it will be connected to this source.")
    utm_medium = fields.Many2one(
        "utm.medium", "Tracking medium",
        help="If the person makes a donation / writes a letter or make a sponsorship "
             "using this link, it will be connected to this channel.")
    utm_campaign = fields.Many2one(
        "utm.campaign", "Tracking campaign",
        help="If the person makes a donation / writes a letter or make a sponsorship "
             "using this link, it will be connected to this campaign.")

    def _compute_country_filter_active(self):
        country_filter_id = self.env["res.config.settings"].get_param(
            "mass_mailing_country_filter_id")
        country_filter = False
        if country_filter_id:
            country_filter = self.env["compassion.field.office"].browse(
                country_filter_id).name
        for wizard in self:
            wizard.country_filter = country_filter

    @api.multi
    def generate_link(self):
        self.ensure_one()
        if not self.base_url:
            raise UserError(_("Please provide a web page to start with."))
        final_url = self.base_url + "?"
        partner = self.partner_id
        next_operator = ""
        if partner:
            if self.sponsorship_id:
                partner = partner.with_context(
                    mailchimp_child=self.sponsorship_id.child_id)
            final_url += partner.wordpress_form_data
            next_operator = "&"
        if self.product_id:
            final_url += next_operator + f"fund_code={self.product_id.default_code}"
            next_operator = "&"
        if self.donation_amount:
            final_url += next_operator + f"fund_amount={self.donation_amount}"
            next_operator = "&"
        if self.utm_source:
            final_url += next_operator + f"utm_source={self.utm_source.name}"
            next_operator = "&"
        if self.utm_medium:
            final_url += next_operator + f"utm_medium={self.utm_medium.name}"
            next_operator = "&"
        if self.utm_campaign:
            final_url += next_operator + f"utm_campaign={self.utm_campaign.name}"
        self.website_link = final_url
        return self._reload()

    @api.multi
    def short_link(self):
        self.ensure_one()
        if not self.website_link:
            result = self.generate_link()
        else:
            result = self._reload()
        tracker = self.env["link.tracker"].create({
            "url": self.website_link,
            "source_id": self.utm_source.id,
            "medium_id": self.utm_medium.id,
            "campaign_id": self.utm_campaign.id
        })
        self.website_link = tracker.short_url
        return result

    def _reload(self):
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "view_type": "form",
            "res_id": self.id,
            "res_model": self._name,
            "target": "new",
            "context": self.env.context,
        }
