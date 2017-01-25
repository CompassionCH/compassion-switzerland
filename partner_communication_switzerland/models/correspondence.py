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
from datetime import datetime

from dateutil.relativedelta import relativedelta

from openerp import models, api, fields


class Correspondence(models.Model):
    _inherit = 'correspondence'

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

    def _compute_letter_format(self):
        """ Letter is zip if it contains a zip attachment"""
        for letter in self:
            if letter.zip_id:
                letter.letter_format = 'zip'
            else:
                super(Correspondence, letter)._compute_letter_format()

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
        :return:
        """
        self.ensure_one()
        if not self.communication_id or self.env.context.get('overwrite'):
            partner = self.correspondant_id
            final_letter = self.env.ref(
                'sbc_compassion.correspondence_type_final')
            if final_letter in self.communication_type_ids:
                template = self.env.ref(
                    'partner_communication_switzerland.final_letter')
            else:
                template = self.env.ref(
                    'partner_communication_switzerland.new_letter')

            # EXCEPTION FOR DEMAUREX : send to Delafontaine
            email = None
            auto_send = self._can_auto_send()
            if partner.ref == '1502623':
                email = 'eric.delafontaine@aligro.ch'
            communication_type = self.env.ref(
                'partner_communication_switzerland.child_letter_config')
            comm_vals = {
                'config_id': communication_type.id,
                'partner_id': partner.id,
                'object_ids': self.id,
                'auto_send': auto_send,
                'email_template_id': template.id,
                'email_to': email,
            }
            if 'comm_vals' in self.env.context:
                comm_vals.update(self.env.context['comm_vals'])
            self.communication_id = self.env[
                'partner.communication.job'].create(comm_vals)
        if self.env.context.get('force_send') and \
                self.communication_id.state != 'done':
            self.communication_id.send()
        return True

    def get_multi_mode(self):
        """
        Tells if we should send the communication with a zip download link
        or with each pdf attached
        :return: true if multi mode should be used
        """
        return len(self) > 3

    @api.model
    def _needaction_domain_get(self):
        ten_days_ago = datetime.today() - relativedelta(days=10)
        domain = [('direction', '=', 'Beneficiary To Supporter'),
                  ('state', '=', 'Published to Global Partner'),
                  ('letter_read', '=', False),
                  ('sent_date', '<', fields.Date.to_string(ten_days_ago))]
        return domain
