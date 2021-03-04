##############################################################################
#
#    Copyright (C) 2018-2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from urllib.parse import urlencode

from odoo import models, api, fields
from odoo.http import request


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _default_odoo_list_ids(self):
        default_val = self.env['mailchimp.lists'].search([])
        return default_val

    odoo_list_ids = fields.Many2many('mailchimp.lists', string='MailChimp Lists', default=_default_odoo_list_ids)
    date_opt_out = fields.Date()
    mailing_contact_ids = fields.One2many(
        "mail.mass_mailing.contact", "partner_id", "Mass Mailing Contacts")

    # Add some computed fields to be used in mailchimp merge fields
    partner_image_url = fields.Char(compute="_compute_partner_image_url")
    wordpress_form_data = fields.Char(compute="_compute_wp_formdata")

    sponsored_child_name = fields.Char(compute="_compute_sponsored_child_fields")
    sponsored_child_reference = fields.Char(compute="_compute_sponsored_child_fields")
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
    def _compute_wp_formdata(self):
        country_filter_id = self.env["res.config.settings"].get_param(
            "mass_mailing_country_filter_id")
        for partner in self:
            locale_partner = partner.with_context(lang=partner.lang)
            child = self.env.context.get("mailchimp_child",
                                         partner.mapped("sponsored_child_ids"))
            if country_filter_id:
                child = child.filtered(
                    lambda c: c.field_office_id.id == country_filter_id)
            data = {
                "firstname": locale_partner.preferred_name,
                "pname": locale_partner.name,
                "email": locale_partner.email,
                "pstreet": locale_partner.street,
                "pcity": locale_partner.city,
                "pzip": locale_partner.zip,
                "pcountry": locale_partner.country_id.name,
                "sponsor_ref": locale_partner.ref,
                "child_ref": child.local_id if len(child) == 1 else False,
            }
            filter_data = {key: val for key, val in data.items() if val}
            partner.wordpress_form_data = urlencode(filter_data)

    @api.multi
    def _compute_sponsored_child_fields(self):
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
            partner.sponsored_child_image = child.filtered(
                'image_url')[:1].thumbnail_url or ''
            partner.sponsored_child_name = child.get_list(
                "preferred_name", 3,
                child.get_number(),
                translate=False)
            partner.sponsored_child_reference = child.get_list("local_id")
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
        elif vals.get("email"):
            partners = super().create(vals)
            vals["partner_id"] = partners.id
            vals["odoo_list_ids"] = partners.odoo_list_ids
            mass_mailing_contact = self.env["mail.mass_mailing.contact"].create(vals)
            mass_mailing_contact.name = partners.firstname + " " + partners.lastname
            mass_mailing_contact.action_export_to_mailchimp()
            return partners
        return super().create(vals)
    @api.multi
    def write(self, vals):
        """
        - Check if contact needs update in mailchimp.
        - Update opt_out date
        - Opt_out from all mailing lists if general opt_out is checked.
        """
        if vals.get("opt_out"):
            vals["date_opt_out"] = fields.Date.today()
        elif "opt_out" in vals:
            vals["date_opt_out"] = False
        base_mailchimp_fields = [
            "email", "lastname", "firstname", "number_sponsorships", "opt_out"]
        update_partner_ids = []
        for contact in self.filtered(lambda c: c.mailing_contact_ids):
            if "opt_out" in vals and vals["opt_out"] != contact.opt_out:
                contact.mailing_contact_ids.mapped("subscription_list_ids")\
                    .with_context(opt_out_from_partner=True).write({
                        "opt_out": vals["opt_out"]})
            if "category_id" in vals:
                contact.mailing_contact_ids.write({
                    "tag_ids": vals["category_id"]
                })
                update_partner_ids.append(contact.id)
            if "email" in vals and not vals["email"]:
                contact.mapped("mailing_contact_ids").filtered(
                    lambda c: c.email == contact.email).unlink()
            mailchimp_fields = contact.mailing_contact_ids.mapped(
                "list_ids.mailchimp_list_id.merge_field_ids.field_id.name")
            mailchimp_fields += base_mailchimp_fields
            for f in mailchimp_fields:
                if f in vals and vals[f] != getattr(contact, f):
                    update_partner_ids.append(contact.id)
                    break
        super().write(vals)
        if vals.get("email") and len(self.mailing_contact_ids) == 0:
            partner = self.filtered(lambda c: c.odoo_list_ids)
            if not partner.opt_out:
                vals["partner_id"] = partner.id
                vals["odoo_list_ids"] = partner.odoo_list_ids
                mass_mailing_contact = self.env["mail.mass_mailing.contact"].create(vals)
                mass_mailing_contact.name = self.firstname + " " + self.lastname
                mass_mailing_contact.action_export_to_mailchimp()
        if update_partner_ids and not self.env.context.get("import_from_mailchimp"):
            self.env["mail.mass_mailing.contact"] \
                .with_delay().update_all_merge_fields_job(update_partner_ids)
        return True

    @api.multi
    def update_selected_child_for_mailchimp(self, child):
        # Allows to force selecting one child for displaying in email templates.
        self.ensure_one()
        for contact in self.with_context(mailchimp_child=child).mailing_contact_ids:
            contact.action_update_to_mailchimp()

    def get_mailing_contact_to_update(self):
        # Only return directly linked contacts
        self.ensure_one()
        return self.mailing_contact_ids

    @api.multi
    def forget_me(self):
        self.mailing_contact_ids.unlink()
        super().forget_me()
        return True
