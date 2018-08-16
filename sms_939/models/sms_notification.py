# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging
import traceback


from odoo import models, api, fields, tools, _

from ..tools import SmsNotificationAnswer


logger = logging.getLogger(__name__)
testing = tools.config.get('test_enable')


class SmsNotification(models.Model):
    _name = 'sms.notification'
    _description = 'SMS Notification'
    _order = 'date desc'

    instance = fields.Char()
    sender = fields.Char(required=True)
    operator = fields.Char()
    service = fields.Char(required=True)
    hook_id = fields.Many2one('sms.hook', 'Hook')
    language = fields.Char()
    date = fields.Datetime()
    uuid = fields.Char()
    text = fields.Char()
    state = fields.Selection([
        ('new', 'Received'),
        ('success', 'Success'),
        ('failed', 'Failed')
    ], default='new')
    failure_details = fields.Text()
    answer = fields.Text()
    partner_id = fields.Many2one('res.partner')

    @api.model
    def create(self, vals):
        # Try to find a matching partner given phone number
        phone = vals.get('sender')
        partner_obj = self.env['res.partner']
        partner = partner_obj.search([('mobile', 'like', phone)]) or \
            partner_obj.search([('phone', 'like', phone)])
        if not partner:
            partner = partner_obj.search([
                ('phone', 'like', phone)
            ])
        if partner and len(partner) == 1:
            vals['partner_id'] = partner.id
        # Attach the hook configuration
        hook = self.env['sms.hook'].search([
            ('name', '=ilike', vals['service'])])
        vals['hook_id'] = hook.id
        sms = super(SmsNotification, self).create(vals)
        if not testing:
            # Directly commit as we don't want to lose SMS in case of failure
            self.env.cr.commit()    # pylint: disable=invalid-commit
        # Return record with language context
        lang = self.env['res.lang'].search([('code', '=', sms.language)],
                                           limit=1)
        sms = sms.with_context(lang=lang and lang.code or 'en_US')
        return sms

    def run_service(self):
        """
        Executes a service when receiving a SMS notification from 939.
        If the function takes more than 15 seconds, it will fail and return
        an error to the sender (to avoid generic error being sent from 939)
        :param params: All request parameters received from 939 web service
        :return: werkzeug.Response object
        """
        self.ensure_one()
        if not self.hook_id:
            hooks = self.env['sms.hook'].search([])
            sms_answer = SmsNotificationAnswer(_(
                "Sorry, we could not understand your request. "
                "Supported services are :\n - %s "
            ) % "\n- ".join(hooks.mapped('name')), costs=0)
            self.write({
                'state': 'failed',
                'failure_details': 'Service is not implemented. '
                'Please configure a hook for this service.',
                'answer': sms_answer.xml_message
            })
            return sms_answer.get_answer()
        service = getattr(self, self.hook_id.func_name)
        try:
            sms_answer = service()
            self.write({
                'state': 'success',
                'answer': sms_answer.xml_message
            })
        except Exception:
            # Abort pending operations
            self.env.cr.rollback()
            self.env.invalidate_all()
            logger.warning("Error processing SMS service", exc_info=True)
            sms_answer = SmsNotificationAnswer(_(
                "Sorry, the service is not available at this time. "
                "Our team is informed and is currently working on it."
            ), costs=0)
            if not testing:
                self.write({
                    'state': 'failed',
                    'failure_details': traceback.format_exc(),
                    'answer': sms_answer.xml_message
                })
        return sms_answer.get_answer()

    def sponsor_service_fr(self):
        return self.with_context(lang='fr_CH').sponsor_service()

    def sponsor_service_de(self):
        return self.with_context(lang='de_DE').sponsor_service()

    def sponsor_service_it(self):
        return self.with_context(lang='it_IT').sponsor_service()

    def sponsor_service(self):
        self.ensure_one()
        # Create a sms child request
        child_request = self.env['sms.child.request'].create({
            'sender': self.sender,
        })
        return SmsNotificationAnswer(
            _("Thank you for your will to help a child ! \n"
              "You can release a child from poverty today by clicking on this "
              "link: %s") % child_request.full_url,
            costs=0
        )

    def test_service(self):
        self.ensure_one()
        return SmsNotificationAnswer("Thanks!", costs=0)

    def test_service_error(self):
        raise Exception
