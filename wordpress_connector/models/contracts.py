# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import re

from odoo.addons.queue_job.job import job, related_action

from odoo import api, models, fields, _
from odoo.tools import config

# Mapping from Website form fields to res.partner fields in Odoo
SPONSOR_MAPPING = {
    'city': 'city',
    'first_name': 'firstname',
    'last_name': 'lastname',
    'zipcode': 'zip',
    'birthday': 'birthdate',
    'Beruf': 'function',
    'phone': 'phone',
    'street': 'street',
    'email': 'email',
    'lang': 'lang'
}

LANG_MAPPING = {
    'fr': 'fr_CH',
    'de': 'de_DE',
    'it': 'it_IT'
}

test_mode = config.get('test_enable')


class Contracts(models.Model):
    _inherit = 'recurring.contract'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    group_id = fields.Many2one(required=False)
    partner_id = fields.Many2one(required=False)

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.model
    def create_sponsorship(self, child_local_id, form_data, sponsor_lang,
                           utm_source, utm_medium, utm_campaign):
        """
        Called by Wordpress to add a new sponsorship.
        :param form_data: all form values entered on the site
        {
            'city': 'Bienne',
            'first_name': 'Emanuel',
            'last_name': 'Cino',
            'language': [u'französich', 'englisch'],
            'zahlungsweise': 'dauerauftrag',
            'consumer_source_text': 'Times Magazine',
            'zipcode': '2503',
            'birthday': '10/04/1989',
            'Beruf': 'Agriculteur paysan',
            'phone': '078 936 45 95',
            'consumer_source': 'Anzeige in Zeitschrift',
            'street': 'Rue test 1',
            'kirchgemeinde': u'Mon église',
            'mithelfen': {
                'checkbox': 'on'
            },
            'salutation': 'Herr',
            'patenschaftplus': {
                'checkbox': 'on'
            },
            'email': 'ecino@compassion.ch',
            'childID': '15783',
            'land': 'Suisse'
        }
        :param child_local_id: local id of child
        :param sponsor_lang: language used in the website
        :param utm_source: identifier from the url tracking
        :param utm_medium: identifier from the url tracking
        :param utm_campaign: identifier from the url tracking
        :return: True if process is good.
        """
        # Add language in data
        form_data['lang'] = LANG_MAPPING[sponsor_lang]

        # Format birthday
        birthday = form_data.get('birthday', '')
        if ('/' in birthday) or (' ' in birthday) or ('.' in birthday) and \
                len(birthday) > 6:
            form_data['birthday'] = birthday[6:] + '-' + birthday[3:5] + \
                '-' + birthday[0:2]

        # Search for existing partner
        partner = self.env['res.partner'].search([
            ('lastname', 'ilike', form_data['last_name']),
            ('firstname', 'ilike', form_data['first_name']),
            ('zip', '=', form_data['zipcode']),
            '|', ('active', '=', True), ('active', '=', False),
        ])
        if partner and len(partner) > 1:
            partner = partner.filtered('has_sponsorships')
            if len(partner) > 1:
                partner = partner.filtered(
                    lambda p: p.email == form_data['email'])
        partner_ok = partner and len(partner) == 1
        if not partner_ok:
            partner = self.create_sponsor_from_web(form_data)
        elif partner.contact_type == 'attached':
            if partner.type == 'email_alias':
                # In this case we want to link to the main partner
                partner = partner.contact_id
            else:
                # We unarchive the partner to make it visible
                partner.active = True

        # Check origin
        internet_id = self.env.ref('utm.utm_medium_website').id
        utms = self.env['utm.mixin'].get_utms(
            utm_source, utm_medium, utm_campaign)

        # Create sponsorship
        child = self.env['compassion.child'].search([
            ('local_id', '=', child_local_id)])
        lines = self._get_sponsorship_standard_lines()
        if not form_data.get('patenschaftplus'):
            lines = lines[:-1]
        sponsorship_vals = {
            'partner_id': partner.id,
            'correspondent_id': partner.id,
            'child_id': child.id,
            'type': 'S',
            'contract_line_ids': lines,
            'next_invoice_date': fields.Date.today(),
            'source_id': utms['source'],
            'medium_id': utms.get('medium', internet_id),
            'campaign_id': utms['campaign'],
        }
        if not test_mode:
            return self.with_delay().create_sponsorship_job(
                sponsorship_vals, form_data)
        else:
            return self.create_sponsorship_job(sponsorship_vals, form_data)

    @api.model
    def create_sponsor_from_web(self, web_data):
        """
        Use the form filled in website to create a new partner.
        :return: view of the partner
        """
        vals = {'state': 'pending'}
        for web_field, odoo_field in SPONSOR_MAPPING.iteritems():
            vals[odoo_field] = web_data.get(web_field)

        # Find the title
        if web_data['salutation'] == 'Herr':
            title = self.env.ref('base.res_partner_title_mister')
        elif web_data['salutation'] == 'Frau':
            title = self.env.ref('base.res_partner_title_madam')
        elif web_data['salutation'] == 'Familie':
            title = self.env.ref(
                'partner_compassion.res_partner_title_family')
        vals['title'] = title.id

        # Find the country
        country = self.env['res.country'].with_context(
            lang=web_data['lang']).search([
                ('name', 'like', web_data['land'])
            ])
        vals['country_id'] = len(country) == 1 and country.id

        # Find language and church
        langs = ','.join(web_data.get('language', ['']))
        sponsor_lang = web_data['lang'][:2]
        church_name = web_data.get('kirchgemeinde')
        vals['spoken_lang_ids'] = self._write_sponsor_lang(
            langs, sponsor_lang)
        church_dict = self._write_church(church_name)
        if church_dict:
            church_field, church_value = church_dict.items()[0]
            vals[church_field] = church_value

        return self.env['res.partner'].create(vals)

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    @api.model
    @job(default_channel='root.child_sync_wp')
    @related_action(action='related_action_contract')
    def create_sponsorship_job(self, values, form_data):
        """
        Creates the wordpress sponsorship.
        :param values: dict for contract creation
        :param form_data: wordpress form data
        :return: <recurring.contract> record
        """
        sponsorship = self.env['recurring.contract'].create(values)
        ambassador_match = re.match(r'^msk_(\d{1,8})', form_data[
            'consumer_source_text'])
        event_match = re.match(r'^msk_(\d{1,8})', form_data[
            'consumer_source'])
        # The sponsorships consumer_source fields were set automatically due
        # to a redirect from the sponsorship button on the muskathlon page.
        if ambassador_match and event_match:
            ambassador_id = int(ambassador_match.group(1))
            event_id = int(event_match.group(1))
            sponsorship.update({
                'user_id': ambassador_id,
                'origin_id': self.env['recurring.contract.origin'].search([
                    ('event_id', '=', event_id)], limit=1).id
            })

        # Notify staff
        sponsor_lang = form_data['lang'][:2]
        staff_param = 'sponsorship_' + sponsor_lang + '_id'
        staff = self.env['staff.notification.settings'].get_param(staff_param)
        notify_text = "A new sponsorship was made on the website. Please " \
                      "verify all information and validate the sponsorship " \
                      "on Odoo: <br/><br/><ul>"

        list_keys = ['salutation', 'first_name', 'last_name', 'birthday',
                     'street', 'zipcode', 'city', 'land', 'email', 'phone',
                     'lang', 'language',
                     'kirchgemeinde', 'Beruf', 'zahlungsweise',
                     'consumer_source', 'consumer_source_text',
                     'patenschaftplus', 'mithelfen', 'childID']

        for key in list_keys:
            notify_text += "<li>" + key + ": " + \
                           unicode(form_data.get(key, '')) + '</li>'

        sponsorship.message_post(
            body=notify_text,
            subject=_('New sponsorship from the website'),
            partner_ids=[staff],
            type='comment',
            subtype='mail.mt_comment',
            content_subtype='html'
        )

        if sponsorship.partner_id.state == 'active':
            # Update sponsor info
            sponsorship.update_partner_from_web_data(form_data)

        sponsorship.partner_id.set_privacy_statement(origin='new_sponsorship')
        return sponsorship

    @api.multi
    def update_partner_from_web_data(self, form_data):
        # Get spoken languages
        self.ensure_one()
        partner = self.partner_id
        sponsor_lang = form_data['lang'][:2]
        langs = ','.join(form_data.get('language', ['']))
        self._write_sponsor_lang(langs, sponsor_lang, partner)

        # Add missing info in partner
        update_fields = ['birthday', 'Beruf', 'phone', 'email']
        partner_vals = dict()
        for field in update_fields:
            odoo_field = SPONSOR_MAPPING[field]
            odoo_val = getattr(partner, odoo_field, False)
            web_val = form_data.get(field)
            if web_val and not odoo_val:
                partner_vals[odoo_field] = web_val
        if partner_vals:
            partner.write(partner_vals)

        # Add church info
        church_name = form_data.get('kirchgemeinde')
        self._write_church(church_name, partner)
        return True

    @api.model
    def _write_sponsor_lang(self, lang_string, sponsor_lang, partner=None):
        """
        Write the sponsor languages given from the website onto a partner
        :param lang_string: selected languages on website, comma separated
        :param sponsor_lang: selected website language
        :param partner: res.partner record
        :return: Odoo write list [(4, lang_id_1), (4, lang_id_2), ...]
        """
        spoken_langs = self.env['res.lang.compassion']
        if 'fra' in lang_string:
            spoken_langs += self.env.ref(
                'child_compassion.lang_compassion_french')
        if sponsor_lang == 'de':
            spoken_langs += self.env.ref(
                'child_switzerland.lang_compassion_german')
        if 'eng' in lang_string:
            spoken_langs += self.env.ref(
                'child_compassion.lang_compassion_english')
        if 'spa' in lang_string:
            spoken_langs += self.env.ref(
                'child_compassion.lang_compassion_spanish')
        if 'por' in lang_string:
            spoken_langs += self.env.ref(
                'child_compassion.lang_compassion_portuguese')
        if 'ita' in lang_string:
            spoken_langs += self.env.ref(
                'child_switzerland.lang_compassion_italian')
        lang_write = [(4, lang.id) for lang in spoken_langs]
        if partner:
            partner.write({'spoken_lang_ids': lang_write})
        return lang_write

    @api.model
    def _write_church(self, church_name, partner=None):
        """
        Write the church in the partner given its name
        :param church_name: church name
        :param partner: res.partner record
        :return: dictionary {odoo_field: odoo_value}
        """
        res = dict()
        if church_name:
            church = self.env['res.partner'].with_context(
                lang='en_US').search([
                    ('name', 'like', church_name),
                    ('category_id.name', '=', 'Church')
                ])
            if len(church) == 1:
                res['church_id'] = church.id
            else:
                res['church_unlinked'] = church_name
        if partner and res and not partner.church_id and \
                not partner.church_unlinked:
            partner.write(res)
        return res
