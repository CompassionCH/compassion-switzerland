##############################################################################
#
#    Copyright (C) 2018-2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, api, fields
from odoo.http import request


class ResPartner(models.Model):
    _inherit = "res.partner"

    date_opt_out = fields.Date()
    mailing_contact_ids = fields.One2many(
        "mail.mass_mailing.contact", "partner_id", "Mass Mailing Contacts")

    # Add some computed fields to be used in mailchimp merge fields
    partner_image_url = fields.Char(compute="_compute_partner_image_url")
    write_link = fields.Char(compute="_compute_wp_links")
    donate_link = fields.Char(compute="_compute_wp_links")

    sponsored_child_name = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_image = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_is = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_was = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_will_be = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_his = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_sein = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_seine = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_seinen = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_seinem = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_seiner = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_ihm = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_ihn = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_son = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_sa = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_ses = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_lui_leur = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_lui_elle = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_le_la = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_your_child = fields.Char(compute="_compute_sponsored_child_fields")

    @api.multi
    def _compute_partner_image_url(self):
        try:
            base_url = request.website.domain
        except AttributeError:
            base_url = self.env["ir.config_parameter"].sudo().get_param(
                "web.external.url")
        for partner in self:
            if partner.image:
                partner.partner_image_url = \
                    f"{base_url}/web/image/res.partner/{partner.id}/image/profile.jpg"

    @api.multi
    def _compute_wp_links(self):
        wp_host = self.env["wordpress.configuration"].sudo().get_host()
        country_filter_id = self.env["res.config.settings"].get_param(
            "mass_mailing_country_filter_id")
        fund_id = self.env["res.config.settings"].get_param(
            "mass_mailing_donation_fund_id")
        for partner in self:
            child = self.env.context.get("mailchimp_child",
                                         partner.mapped("sponsored_child_ids"))
            if country_filter_id:
                child = child.filtered(
                    lambda c: c.field_office_id.id == country_filter_id)
            write_link =\
                f"https://{wp_host}/ecrire#email={partner.email}" \
                f"&pname={partner.preferred_name}&sponsor_ref={partner.ref}"
            donate_link = \
                f"https://{wp_host}/formulaire-pour-dons#last_name={partner.lastname}&" \
                f"first_name={partner.firstname}&street={partner.street}" \
                f"&zipcode={partner.zip}&city={partner.city}&email={partner.email}"
            if fund_id:
                donation_code = self.env[
                    "product.template"].sudo().browse(fund_id).default_code
                donate_link += f"&fonds={donation_code}"
            if len(child) == 1:
                write_link += f"&child_ref={child.local_id}"
                donate_link += f"&refenfant={child.local_id}"
            partner.write_link = write_link
            partner.donate_link = donate_link

    @api.multi
    def _compute_sponsored_child_fields(self):
        try:
            base_url = request.website.domain
        except AttributeError:
            base_url = self.env["ir.config_parameter"].sudo().get_param(
                "web.external.url")
        base_url += "/web/image/compassion.child.pictures"
        country_filter_id = self.env["res.config.settings"].get_param(
            "mass_mailing_country_filter_id")
        for partner in self:
            lang_partner = partner.with_context(lang=partner.lang)
            # Allow option to take a child given in context, otherwise take
            # the sponsored children.
            child = self.env.context.get("mailchimp_child",
                                         lang_partner.mapped("sponsored_child_ids"))
            if country_filter_id:
                child = child.filtered(
                    lambda c: c.field_office_id.id == country_filter_id)
            last_image = child.mapped("pictures_ids")[:1]
            if last_image:
                partner.sponsored_child_image = \
                    f"{base_url}/{last_image.id}/headshot" \
                    f"/{last_image.child_id.local_id}-portrait.jpg"
            partner.sponsored_child_name = child.get_list(
                "preferred_name", 3,
                child.get("many children"),
                translate=False)
            partner.sponsored_child_is = child.get("is")
            partner.sponsored_child_was = child.get("was")
            partner.sponsored_child_will_be = child.get("will be")
            partner.sponsored_child_he = child.get("he")
            partner.sponsored_child_his = child.get("his")
            partner.sponsored_child_sein = child.get("sein")
            partner.sponsored_child_seine = child.get("seine")
            partner.sponsored_child_seinen = child.get("seinen")
            partner.sponsored_child_seinem = child.get("seinem")
            partner.sponsored_child_seiner = child.get("seiner")
            partner.sponsored_child_ihm = child.get("ihm")
            partner.sponsored_child_ihn = child.get("ihn")
            partner.sponsored_child_son = child.get("son")
            partner.sponsored_child_sa = child.get("sa")
            partner.sponsored_child_ses = child.get("ses")
            partner.sponsored_child_lui_leur = child.get("lui_leur")
            partner.sponsored_child_lui_elle = child.get("lui_elle")
            partner.sponsored_child_le_la = child.get("le_la")
            partner.sponsored_child_your_child = child.get("your sponsored child")

    @api.model
    def create(self, vals):
        if vals.get("opt_out"):
            vals["date_opt_out"] = fields.Date.today()
        return super().create(vals)

    @api.multi
    def write(self, vals):
        if vals.get("opt_out"):
            vals["date_opt_out"] = fields.Date.today()
        elif "opt_out" in vals:
            vals["date_opt_out"] = False
        return super().write(vals)

    @api.multi
    def update_selected_child_for_mailchimp(self, child):
        # Allows to force selecting one child for displaying in email templates.
        self.ensure_one()
        for contact in self.with_context(mailchimp_child=child).mailing_contact_ids:
            contact.action_update_to_mailchimp()
