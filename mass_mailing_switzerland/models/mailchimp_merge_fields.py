##############################################################################
#
#    Copyright (C) 2021 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import fields, models


class MailchimpMergeFields(models.Model):
    _inherit = "mailchimp.merge.fields"

    # Allows to use fields from mail.mass_mailing.contact records in merge fields
    field_id = fields.Many2one(domain=[
        ('model_id.model', 'in', ['res.partner', 'mail.mass_mailing.contact']),
        ('ttype', 'not in', ['one2many', 'many2one', 'many2many'])]
    )

    def get_value(self, mailing_contact):
        contact_fields = self.filtered(
            lambda f: f.field_id.model == "mail.mass_mailing.contact")
        partner_fields = self - contact_fields
        res = super(MailchimpMergeFields, partner_fields).get_value(mailing_contact)
        for custom_field in contact_fields:
            if custom_field.field_id and hasattr(
                    self, custom_field.field_id.name):
                value = getattr(self, custom_field.field_id.name)
            else:
                value = ''
            res.update({custom_field.tag: value or ''})
        return res
