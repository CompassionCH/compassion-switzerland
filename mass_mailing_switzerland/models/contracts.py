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
import simplejson

from odoo.addons.child_compassion.models.compassion_hold import HoldType
from odoo.addons.queue_job.job import job, related_action

from odoo import api, models, fields

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


class Contracts(models.Model):
    _inherit = 'recurring.contract'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    web_data = fields.Text(help='Form data filled from website')
    group_id = fields.Many2one(required=False)
    partner_id = fields.Many2one(required=False)
    mailing_campaign_id = fields.Many2one('mail.mass_mailing.campaign')

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.model
    def create_sponsorship(self, child_local_id, form_data, sponsor_lang,
                           mailing_slug):
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
            'email':
                'ecino@compassion.ch',
            'childID':
                '15783',
            'land': 'Suisse'
        }
        :param child_local_id: local id of child
        :param sponsor_lang: language used in the website
        :param mailing_slug: slug of the mailing campaign
        :return: True if process is good.
        """
        # Format birthday
        birthday = form_data.get('birthday', '')
        if ('/' in birthday) or (' ' in birthday) or ('.' in birthday) and \
                len(birthday) > 6:
            form_data['birthday'] = birthday[6:] + '-' + birthday[3:5] + \
                '-' + birthday[0:2]

        # Search for existing partner
        partner = self.env['res.partner'].search([
            ('lastname', 'like', form_data['last_name']),
            ('firstname', 'like', form_data['first_name']),
            ('zip', '=', form_data['zipcode'])
        ])
        if partner and len(partner) > 1:
            partner = partner.filtered('has_sponsorships')
        partner_ok = partner and len(partner) == 1

        # Check origin
        campaign_id = False
        if mailing_slug:
            campaign_id = self.env['mail.mass_mailing.campaign'].search([
                ('mailing_slug', '=', mailing_slug)
            ], limit=1).id
        # Create sponsorship
        child = self.env['compassion.child'].search([
            ('local_id', '=', child_local_id)])
        lines = self._get_sponsorship_standard_lines()
        if not form_data.get('patenschaftplus'):
            lines = lines[:-1]
        form_data['lang'] = LANG_MAPPING[sponsor_lang]
        sponsorship = self.create({
            'partner_id': partner_ok and partner.id,
            'correspondant_id': partner_ok and partner.id,
            'child_id': child.id,
            'web_data': simplejson.dumps(form_data),
            'type': 'S',
            'contract_line_ids': lines,
            'next_invoice_date': fields.Date.today(),
            'channel': 'internet',
            'mailing_campaign_id': campaign_id,
        })

        # Notify staff
        staff_param = 'sponsorship_' + sponsor_lang + '_id'
        staff = self.env['staff.notification.settings'].get_param(staff_param)
        notify_text = "A new sponsorship was made on the website. Please " \
                      "verify all information and validate the sponsorship " \
                      "on Odoo: <br/><br/><ul>"
        for field, value in form_data.iteritems():
            notify_text += "<li>" + field + ': ' + unicode(value) + '</li>'
        sponsorship.message_post(
            body=notify_text,
            subject="New sponsorship from the website",
            partner_ids=[staff],
            type='comment',
            subtype='mail.mt_comment',
            content_subtype='html'
        )

        if partner_ok:
            # Update sponsor info
            sponsorship.with_delay().update_partner_from_web_data()

        # Convert to No Money Hold
        sponsorship.with_delay().update_child_hold()

        return True

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def create_sponsor_from_web(self):
        """
        Use the form filled in website to create a new partner.
        :return: view of the partner
        """
        self.ensure_one()
        form_data = simplejson.loads(self.web_data)
        vals = dict()
        for web_field, odoo_field in SPONSOR_MAPPING.iteritems():
            vals[odoo_field] = form_data.get(web_field)

        # Find the title
        if form_data['salutation'] == 'Herr':
            title = self.env.ref('base.res_partner_title_mister')
        elif form_data['salutation'] == 'Frau':
            title = self.env.ref('base.res_partner_title_madam')
        elif form_data['salutation'] == 'Familie':
            title = self.env.ref(
                'partner_compassion.res_partner_title_family')
        vals['title'] = title.id

        # Find the country
        country = self.env['res.country'].with_context(
            lang=form_data['lang']).search([
                ('name', 'like', form_data['land'])
            ])
        vals['country_id'] = len(country) == 1 and country.id

        # Find language and church
        langs = ','.join(form_data.get('language', ['']))
        sponsor_lang = form_data['lang'][:2]
        church_name = form_data.get('kirchgemeinde')
        vals['spoken_lang_ids'] = self._write_sponsor_lang(
            langs, sponsor_lang)
        church_dict = self._write_church(church_name)
        if church_dict:
            church_field, church_value = church_dict.items()[0]
            vals[church_field] = church_value

        partner = self.env['res.partner'].with_context(
            default_type=None).create(vals)
        self.write({
            'partner_id': partner.id,
            'correspondant_id': partner.id,
            'web_data': False,
        })
        self.child_id.sponsor_id = partner

        return {
            'name': partner.name,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'res.partner',
            'res_id': partner.id,
            'context': self.env.context,
            'target': 'current',
        }

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    @api.multi
    @job(default_channel='root.child_sync_wp')
    @related_action(action='related_action_sponsorship')
    def update_partner_from_web_data(self):
        # Get spoken languages
        self.ensure_one()
        form_data = simplejson.loads(self.web_data)
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

    @api.multi
    @job(default_channel='root.child_sync_wp')
    @related_action(action='related_action_sponsorship')
    def update_child_hold(self):
        # Convert to No Money Hold
        self.ensure_one()
        return self.child_id.hold_id.write({
            'expiration_date': self.env[
                'compassion.hold'].get_default_hold_expiration(
                HoldType.NO_MONEY_HOLD),
            'type': HoldType.NO_MONEY_HOLD.value,
        })

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
        lang_module = 'child_compassion.'
        if 'fra' in lang_string:
            spoken_langs += self.env.ref(
                lang_module + 'lang_compassion_french')
        if sponsor_lang == 'de':
            spoken_langs += self.env.ref(
                lang_module + 'lang_compassion_german')
        if 'eng' in lang_string:
            spoken_langs += self.env.ref(
                lang_module + 'lang_compassion_english')
        if 'spa' in lang_string:
            spoken_langs += self.env.ref(
                lang_module + 'lang_compassion_spanish')
        if 'por' in lang_string:
            spoken_langs += self.env.ref(
                lang_module + 'lang_compassion_portuguese')
        if 'ita' in lang_string:
            spoken_langs += self.env.ref(
                lang_module + 'lang_compassion_italian')
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
