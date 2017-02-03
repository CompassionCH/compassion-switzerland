# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import base64
import detectlanguage

from datetime import datetime
from dateutil.relativedelta import relativedelta

from openerp import models, api, fields


class Correspondence(models.Model):
    _inherit = 'correspondence'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    communication_id = fields.Many2one(
        'partner.communication.job', 'Communication')
    email_id = fields.Many2one(
        'mail.mail', 'E-mail', related='communication_id.email_id',
        store=True)
    communication_state = fields.Selection(related='communication_id.state')
    sent_date = fields.Datetime(
        'Communication sent', related='communication_id.sent_date',
        store=True, track_visibility='onchange')
    email_read = fields.Boolean()
    letter_read = fields.Boolean()
    zip_id = fields.Many2one('ir.attachment')
    has_valid_language = fields.Boolean(compute='_compute_has_valid_language')

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    def _compute_letter_format(self):
        """ Letter is zip if it contains a zip attachment"""
        for letter in self:
            if letter.zip_id:
                letter.letter_format = 'zip'
            else:
                super(Correspondence, letter)._compute_letter_format()

    @api.one
    def _compute_has_valid_language(self):
        """ Detect if text is written in the language corresponding to the
        language_id """
        self.has_valid_language = False
        if self.translated_text is not None and \
                        self.translation_language_id is not None:
            s = self.translated_text.strip(' \t\n\r.')
            if s:
                # find the language name of text argument
                detectlanguage.configuration.api_key = config.get(
                    'detect_language_api_key')
                languageName = ""
                langs = detectlanguage.languages()
                try:
                    codeLang = detectlanguage.simple_detect(
                        self.translated_text)
                except IndexError:
                    # Language could not be detected
                    return
                for lang in langs:
                    if lang.get("code") == codeLang:
                        languageName = lang.get("name").lower()
                        break
                supporter_langs = map(
                    lambda lang: lang.lower(),
                    self.supporter_languages_ids.mapped('name'))
                self.has_valid_language = languageName in supporter_langs

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def get_image(self):
        """ Method for retrieving the image """
        self.ensure_one()
        if self.zip_id:
            data = base64.b64decode(self.zip_id.datas)
        else:
            data = super(Correspondence, self).get_image()
        return data

    @api.multi
    def attach_zip(self):
        """
        When a partner gets multiple letters, we make a zip and attach it
        to the first letter, so that he can only download this zip.
        :return: True
        """
        _zip = self.env['correspondence.download.wizard'].with_context(
            active_model=self._name, active_ids=self.ids).create({})
        self.mapped('zip_id').unlink()
        letter_zip = self[0]
        other_letters = self - letter_zip
        base_url = self.env['ir.config_parameter'].get_param(
            'web.external.url')
        letter_zip.zip_id = self.env['ir.attachment'].create({
            'datas': _zip.download_data,
            'name': _zip.fname,
            'res_id': letter_zip.id,
            'res_model': self._name,
            'datas_fname': _zip.fname,
        })
        letter_zip.read_url = "{}/b2s_image?id={}".format(
            base_url, letter_zip.uuid)
        other_letters.write({'read_url': False, 'zip_id': False})
        return True

    @api.multi
    def send_communication(self):
        """
        Sends the communication to the partner. By default it won't do
        anything if a communication is already attached to the letter.
        Context can contain following settings :
            - comm_vals : dictionary for communication values
            - force_send : will send the communication regardless of the
                           settings.
            - overwrite : will force the communication creation even if one
                          already exists.
        :return: True
        """
        partners = self.mapped('correspondant_id')
        final_letter = self.env.ref(
            'sbc_compassion.correspondence_type_final')
        final_template = self.env.ref(
            'partner_communication_switzerland.child_letter_final_config')
        new_template = self.env.ref(
            'partner_communication_switzerland.child_letter_config')
        old_template = self.env.ref(
            'partner_communication_switzerland.child_letter_old_config')
        old_limit = datetime.today() - relativedelta(months=1)

        for partner in partners:
            letters = self.filtered(lambda l: l.correspondant_id == partner)
            no_comm = letters.filtered(lambda l: not l.communication_id)
            to_generate = letters if self.env.context.get(
                'overwrite') else no_comm

            final_letters = to_generate.filtered(
                lambda l: final_letter in l.communication_type_ids)
            new_letters = to_generate - final_letters
            old_letters = new_letters.filtered(
                lambda l: fields.Datetime.from_string(l.status_date) <
                old_limit
            )
            new_letters -= old_letters

            final_letters._generate_communication(final_template.id)
            new_letters._generate_communication(new_template.id)
            old_letters._generate_communication(old_template.id)

        if self.env.context.get('force_send'):
            self.mapped('communication_id').filtered(
                lambda c: c.state != 'done').send()

        return True

    def get_multi_mode(self):
        """
        Tells if we should send the communication with a zip download link
        or with each pdf attached
        :return: true if multi mode should be used
        """
        return len(self) > 3

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _generate_communication(self, config_id):
        """
        Generates the communication for given letters.
        :param config_id: partner.communication.config id
        :return: True
        """
        if not self:
            return True

        partner = self.mapped('correspondant_id')
        auto_send = [l._can_auto_send() for l in self]
        auto_send = reduce(lambda l1, l2: l1 and l2, auto_send)
        comm_vals = {
            'partner_id': partner.id,
            'config_id': config_id,
            'object_ids': self.ids,
            'auto_send': auto_send
        }
        # EXCEPTION FOR DEMAUREX : send to Delafontaine
        if partner.ref == '1502623':
            comm_vals['email_to'] = 'eric.delafontaine@aligro.ch'

        if 'comm_vals' in self.env.context:
            comm_vals.update(self.env.context['comm_vals'])

        comm_obj = self.env['partner.communication.job']
        return self.write({
            'communication_id': comm_obj.create(comm_vals).id
        })

    @api.model
    def _needaction_domain_get(self):
        ten_days_ago = datetime.today() - relativedelta(days=10)
        domain = [('direction', '=', 'Beneficiary To Supporter'),
                  ('state', '=', 'Published to Global Partner'),
                  ('letter_read', '=', False),
                  ('sent_date', '<', fields.Date.to_string(ten_days_ago))]
        return domain

    def _can_auto_send(self):
        """ Tells if we can automatically send the letter by e-mail or should
        require manual validation before.
        """
        self.ensure_one()
        partner_langs = self.supporter_languages_ids
        common = partner_langs & self.beneficiary_language_ids
        if common:
            types = self.communication_type_ids.mapped('name')
            valid = (
                self.sponsorship_id.state == 'active' and
                'Final Letter' not in types and
                'auto' in self.correspondant_id.letter_delivery_preference
            )
        else:
            valid = self.has_valid_language and 'auto' in \
                self.correspondant_id.letter_delivery_preference

        return valid
