##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, tools, api, _

testing = tools.config.get('test_enable')


if not testing:
    class PartnerSmsRegistrationForm(models.AbstractModel):
        _inherit = 'cms.form.recurring.contract'

        # Only propose LSV, Direct Debit and Permanent Order
        payment_mode_id = fields.Many2one(
            'account.payment.mode',
            string='Payment mode',
            domain=lambda self: self._get_domain())

        spoken_lang_en = fields.Boolean('English')
        spoken_lang_fr = fields.Boolean('French')
        spoken_lang_es = fields.Boolean('Spanish')
        spoken_lang_po = fields.Boolean('Portuguese')
        partner_church_unlinked = fields.Char('Church')
        partner_function = fields.Char('Job')
        volunteering = fields.Boolean(
            'Send me information about volunteering with Compassion')

        @api.model
        def _get_domain(self):

            lsv = self.env.ref('sponsorship_switzerland.payment_mode_lsv').ids
            dd = self.env.ref(
                'sponsorship_switzerland.payment_mode_postfinance_dd').ids
            po = self.env.ref(
                'sponsorship_switzerland.payment_mode_permanent_order').ids

            return [('id', 'in', lsv + dd + po)]

        @property
        def _form_fieldsets(self):
            fieldset = super()._form_fieldsets
            fieldset[0]['fields'].extend([
                'partner_function', 'partner_church_unlinked'])
            fieldset.insert(2, {
                'id': 'volunteering',
                'title': _('Volunteering'),
                'fields': ['volunteering'],
            })
            sponsor_langs = self.partner_id.sudo().spoken_lang_ids
            child_langs = self.main_object.sudo().child_id. \
                field_office_id.spoken_language_ids.filtered('translatable')
            lang_en = self.env.ref('child_compassion.lang_compassion_english')
            if lang_en not in sponsor_langs or not (child_langs &
                                                    sponsor_langs):
                lang_po = self.env.ref(
                    'child_compassion.lang_compassion_portuguese')
                lang_fr = self.env.ref(
                    'child_compassion.lang_compassion_french')
                lang_es = self.env.ref(
                    'child_compassion.lang_compassion_spanish')
                _fields = []
                if lang_en not in sponsor_langs:
                    _fields.append('spoken_lang_en')
                if lang_fr in child_langs and lang_fr not in sponsor_langs:
                    _fields.append('spoken_lang_fr')
                if lang_es in child_langs and lang_es not in sponsor_langs:
                    _fields.append('spoken_lang_es')
                if lang_po in child_langs and lang_po not in sponsor_langs:
                    _fields.append('spoken_lang_po')
                fieldset.insert(1, {
                    'id': 'correspondence',
                    'title': _('Letters exchange'),
                    'description': _(
                        'We are happy to translate letters for you and your '
                        'sponsored child. In case you know his language or '
                        'English, please indicate it below; this will save '
                        'time on sending the letters.'),
                    'fields': _fields,
                })
            return fieldset

        def _form_load_partner_function(self, fname, field, value,
                                        **req_values):
            return value or self._load_partner_field(fname, **req_values)

        def _form_load_partner_church_unlinked(self, fname, field, value,
                                               **req_values):
            res = value
            if not res:
                res = self._load_partner_field(
                    'partner_church_id', **req_values)
                if res and isinstance(res, models.Model):
                    res = res.name
                else:
                    res = self._load_partner_field(fname, **req_values)
            return res

        def _get_partner_vals(self, values, extra_values):
            # Add spoken languages
            result = super()._get_partner_vals(values, extra_values)
            spoken_langs = []
            if extra_values.get('spoken_lang_en'):
                spoken_langs.append(
                    self.env.ref(
                        'child_compassion.lang_compassion_english').id
                )
            if extra_values.get('spoken_lang_fr'):
                spoken_langs.append(
                    self.env.ref(
                        'child_compassion.lang_compassion_french').id
                )
            if extra_values.get('spoken_lang_es'):
                spoken_langs.append(
                    self.env.ref(
                        'child_compassion.lang_compassion_spanish').id
                )
            if extra_values.get('spoken_lang_po'):
                spoken_langs.append(
                    self.env.ref(
                        'child_compassion.lang_compassion_portuguese').id
                )
            if spoken_langs:
                result['spoken_lang_ids'] = [(4, sid) for sid in spoken_langs]
            return result

        def _get_post_message_values(self, form_vals):
            vals = super()._get_post_message_values(form_vals)
            church = form_vals.get('partner_church_unlinked')
            if church:
                vals['Church'] = church
            vals['Volunteering'] = form_vals.get('volunteering') and \
                'Yes' or 'No'
            return vals

        def _get_partner_keys(self):
            res = super()._get_partner_keys()
            res.extend(['church_unlinked', 'function'])
            return res
