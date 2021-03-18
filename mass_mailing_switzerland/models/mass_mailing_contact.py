##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
#
#
from time import sleep
from odoo import api, models, fields
from odoo.addons.queue_job.job import job


def _partner_split_name(partner_name):
    return [' '.join(partner_name.split()[:-1]), ' '.join(partner_name.split()[-1:])]


def _filter_criteria(element, partner_to_update):
    if not partner_to_update:
        return True
    else:
        if len(element) == 1:
            element = [element]
        return any(x.id in partner_to_update for x in element)


class MassMailingContact(models.Model):
    _inherit = "mail.mass_mailing.contact"

    partner_ids = fields.Many2many(
        "res.partner", "mass_mailing_contact_partner_rel", "partner_ids", "mass_mailing_contact_ids",
        string="Associated contacts", readonly=False
    )
    partner_id = fields.Many2one(
        "res.partner", "Associated contact", ondelete="cascade",
    )
    merged_child = fields.Char(default="")
    merged_salutation = fields.Char(default="")

    @api.model
    def move_m2o_to_m2m(self):
        i = 0
        print("Start Update")
        for rec in self.search(
                [('partner_id', '!=', False)]):  # Search all the records that have value in m2o field
            i = i + 1
            if i % 10 == 0:
                print(i)
            if not rec.partner_ids:
                rec.add_partners(rec.partner_id.id)
            else:
                print("already" + str(i))
        return True

    @api.multi
    def compute_sponsored_child_fields(self):
        for record in self.filtered(lambda c: c.partner_ids):
            partner_ids = record.partner_ids
            country_filter_id = self.env["res.config.settings"].get_param(
                "mass_mailing_country_filter_id")
            lang_partner = partner_ids.with_context(lang=partner_ids[0].lang)
            # Allow option to take a child given in context, otherwise take
            # the sponsored children.
            child = self.env.context.get("mailchimp_child",
                                         lang_partner.mapped("sponsored_child_ids"))
            if country_filter_id:
                child = child.filtered(
                    lambda c: c.field_office_id.id == country_filter_id)
            children_names = child.get_list(
                "preferred_name", 3,
                child.get_number(),
                translate=False)
            if len(children_names) != 0:
                record.write({"merged_child": children_names})

    @api.multi
    def compute_tags(self):
        for record in self.filtered(lambda c: c.partner_ids):
            tags = record.partner_ids.mapped("category_id")
            if tags:
                record.write({"tag_ids": [[6, False, [i.id for i in tags]]]})

    @api.multi
    def compute_salutation(self):
        for record in self.filtered(lambda c: c.partner_ids):
            partner_ids = record.partner_ids
            if len(partner_ids) == 1:
                salutation = partner_ids[0].full_salutation
            elif partner_ids[0].lastname == partner_ids[1].lastname:
                lang_partner = partner_ids[0].with_context(lang=partner_ids[0].lang)
                title = lang_partner.title
                title_salutation = (
                    lang_partner.env["ir.advanced.translation"]
                        .get("salutation", female=title.gender == "F", plural=title.plural)
                        .title()
                )
                family_title = self.env.ref("partner_compassion.res_partner_title_family")
                salutation = title_salutation + " " + family_title.name + " " + lang_partner.lastname
            else:
                partners = partner_ids.with_context(lang=partner_ids[0].lang)
                if partners.search([("title.gender", "=", "M")]):
                    title_salutation = (
                        partners.env["ir.advanced.translation"]
                            .get("salutation", female=False, plural=True)
                            .title()
                    )
                else:
                    title_salutation = (
                        partners.env["ir.advanced.translation"]
                            .get("salutation", female=True, plural=True)
                            .title()
                    )
                salutation = title_salutation + " " + partners.get_list('name', translate=False)
            record.write({'merged_salutation': salutation})

    @api.multi
    def add_partners(self, partner_ids):
        for contact in self:
            if type(partner_ids) != list:
                partner_ids = [partner_ids]
            contact.write({"partner_ids": [(4, partner_id) for partner_id in partner_ids]})
            partner_ids = contact.partner_ids
            contact.compute_tags()
            contact.compute_sponsored_child_fields()
            contact.compute_salutation()
            if partner_ids[0].firstname and partner_ids[0].lastname:
                contact.write({"name": partner_ids[0].firstname + " " + partner_ids[0].lastname})
            else:
                contact.write({"name": partner_ids[0].lastname})


    @api.multi
    def remove_partner(self, partner_ids):
        for contact in self:
            print("contact")
            if type(partner_ids) != list:
                partner_ids = [partner_ids]
            contact.write({"partner_ids": [(3, partner_id) for partner_id in partner_ids]})
            partner_ids = contact.partner_ids
            if partner_ids:
                contact.compute_tags()
                contact.compute_sponsored_child_fields()
                contact.compute_salutation()
                contact.write({"name": partner_ids[0].firstname + " " + partner_ids[0].lastname})
            else:
                contact.unlink()

    @api.model
    def create(self, vals_list):
        if 'partner_id' in vals_list:
            contact = self.env['mail.mass_mailing.contact'].search([('email', '=', vals_list['email'])], limit=1)
            if contact:
                contact.add_partners(vals_list['partner_id'])
                return None
        records = super().create(vals_list)
        for contact in records:
            if 'partner_id' in vals_list:
                contact.add_partners(vals_list['partner_id'])
            else:
                partner = contact.get_partner(contact.email)
                if partner:
                    contact.write({"partner_ids": [(4, partner)]})
            if 'odoo_list_ids' in vals_list:
                for odoo_list_id in vals_list['odoo_list_ids']:
                    vals = {'list_id': odoo_list_id.odoo_list_id.id, 'contact_id': contact.id}
                    contact.subscription_list_ids.create(vals)
        records.action_export_to_mailchimp()
        return records

    @api.multi
    def write(self, values):
        super().write(values)
        if "partner_ids" in values:
            for contact in self.filtered(lambda c: c.partner_ids):
                contact.compute_salutation()
                contact.compute_sponsored_child_fields()
                contact.action_update_to_mailchimp()
        return True

    @api.multi
    def _prepare_vals_for_merge_fields(self, mailchimp_list_id):
        merge_fields_vals = {}
        partner_id = self.partner_id
        test = mailchimp_list_id.merge_field_ids
        for custom_field in mailchimp_list_id.merge_field_ids:
            if custom_field.field_id.model == "mail.mass_mailing.contact":
                if custom_field.field_id and hasattr(
                        self, custom_field.field_id.name):
                    value = getattr(self, custom_field.field_id.name)
                else:
                    value = ''
                merge_fields_vals.update({custom_field.tag: value or ''})

            else:
                if custom_field.type == 'address' and partner_id:
                    address = {'addr1': partner_id.street or '',
                               'addr2': partner_id.street2 or '',
                               'city': partner_id.city or '',
                               'state': partner_id.state_id.name if partner_id.state_id else '',
                               'zip': partner_id.zip or '',
                               'country': partner_id.country_id.code if partner_id.country_id else ''}
                    merge_fields_vals.update({custom_field.tag: address})
                elif custom_field.tag == 'FNAME':
                    merge_fields_vals.update({custom_field.tag: _partner_split_name(self.name)[0] if
                    _partner_split_name(self.name)[0] else _partner_split_name(self.name)[1]})
                elif custom_field.tag == 'LNAME':
                    merge_fields_vals.update({custom_field.tag: _partner_split_name(self.name)[1] if
                    _partner_split_name(self.name)[0] else _partner_split_name(self.name)[0]})
                elif custom_field.type in ['date', 'birthday']:
                    value = getattr(partner_id or self,
                                    custom_field.field_id.name) if custom_field.field_id and hasattr(
                        partner_id or self, custom_field.field_id.name) else ''
                    if value:
                        value = value.strftime(custom_field.date_format)
                    merge_fields_vals.update({custom_field.tag: value or ''})
                else:
                    value = getattr(partner_id or self,
                                    custom_field.field_id.name) if custom_field.field_id and hasattr(
                        partner_id or self, custom_field.field_id.name) else ''
                    if custom_field.type == 'text' and not isinstance(value, str):
                        value = str(value)
                    merge_fields_vals.update({custom_field.tag: value or ''})
        return merge_fields_vals

    @api.multi
    def get_partner(self, email):
        """Override to fetch partner directly from relation if set."""
        self.ensure_one()
        if self.partner_ids:
            return self.partner_ids[0].id
        else:
            return self.env["res.partner"].search([
                ("email", "=ilike", email),
                ("contact_type", "=", "standalone"),
                ("opt_out", "!=", True)
            ], limit=1).id

    @job(default_channel="root.mass_mailing_switzerland.update_mailchimp")
    @api.model
    def update_all_merge_fields_job(self, partner_to_update=None):
        """ Update all contacts merge fields
        :return: List of partner_ids that failed to update
        """
        search_criterias = [("partner_id", "!=", False)]
        failed = []
        for mailing_contact in self.search(search_criterias).filtered(
                lambda a: _filter_criteria(a.partner_ids, partner_to_update)):
            try:
                mailing_contact.action_update_to_mailchimp()
            except:
                self.env.clear()
                for partner in mailing_contact.partner_ids:
                    if partner_to_update and partner in partner_to_update:
                        failed.append(partner.id)
                    elif not partner_to_update:
                        failed.append(partner.id)
                # Allows network to recover
                sleep(1)
        return failed

    @api.multi
    def action_export_to_mailchimp(self):
        """
        Always export in english so that all tags are set in English
        """
        if self.env.context.get("skip_mailchimp"):
            return True
        return super(MassMailingContact,
                     self.with_context(lang="en_US")).action_export_to_mailchimp()

    @api.multi
    def action_update_to_mailchimp(self):
        """
        Always export in english so that all tags are set in English
        """
        if self.env.context.get("skip_mailchimp"):
            return True
        return super(MassMailingContact,
                     self.with_context(lang="en_US")).action_update_to_mailchimp()

    @api.multi
    def action_archive_from_mailchimp(self):
        available_mailchimp_lists = self.env['mailchimp.lists'].search([])
        lists = available_mailchimp_lists.mapped('odoo_list_id').ids
        for record in self:
            lists_to_export = record.subscription_list_ids.filtered(
                lambda x: x.list_id.id in lists and x.mailchimp_id)
            for list in lists_to_export:
                mailchimp_list_id = list.list_id.mailchimp_list_id
                val = mailchimp_list_id.account_id._send_request(
                    'search-members?query=%s&field=exact_matches' % list.contact_id.email, {
                    }, method='GET')
                for member in val['exact_matches']['members']:
                    if member['id'] == list.md5_email and member['status'] != 'archived':
                        mailchimp_list_id.account_id._send_request(
                            'lists/%s/members/%s' % (mailchimp_list_id.list_id, list.md5_email),
                            {}, method='DELETE')
        return True

    @api.multi
    def unlink(self):
        self.action_archive_from_mailchimp()
        return super().unlink()
