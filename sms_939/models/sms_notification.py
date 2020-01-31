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
from odoo.addons.queue_job.job import job

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
    language = fields.Char(required=True)
    date = fields.Datetime(default=fields.Datetime.now)
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
        partner = partner_obj.search(
            ['|', ('mobile', 'like', phone),
             ('phone', 'like', phone),
             ('active', 'in', [True, False])])
        if partner and len(partner) == 1:
            vals['partner_id'] = partner.id
            vals['language'] = partner.lang
            partner.active = True
        # Attach the hook configuration
        hook = self.env['sms.hook'].search([
            ('name', '=ilike', vals['service'])])
        vals['hook_id'] = hook.id
        if not testing:
            # Directly commit as we don't want to lose SMS in case of failure
            self.env.cr.commit()    # pylint: disable=invalid-commit
        # Return record with language context
        langs = self.env['res.lang'] \
            .search([('code', '=ilike', vals['language'] + '%')], limit=1) \
            if 'language' in vals and vals['language'] else ()
        lang_or_en = next((lang.code for lang in langs), 'en_US')
        vals['language'] = lang_or_en

        sms = super().create(vals)
        sms = sms.with_context(lang=lang_or_en)
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
        sms_receipient = self.sender
        sms_text = self.text or ''
        if not self.hook_id:
            hooks = self.env['sms.hook'].search([])
            n1 = "\n"
            sms_answer = _(
                "Sorry, we could not understand your request. "
                f"Supported services are :\n - {n1 + '- '.join(hooks.mapped('name'))}"
            )
            self.write({
                'state': 'failed',
                'failure_details': 'Service is not implemented. '
                'Please configure a hook for this service.',
                'answer': sms_answer
            })
        else:
            service = getattr(self, self.hook_id.__name__)
            # service = getattr(self, self.hook_id.func_name)
            try:
                sms_answer = service()
                self.write({
                    'state': 'success',
                    'answer': sms_answer
                })
            except Exception:
                # Abort pending operations
                self.env.cr.rollback()
                self.env.clear()
                logger.warning("Error processing SMS service", exc_info=True)
                sms_answer = _(
                    "Sorry, the service is not available at this time. "
                    "Our team is informed and is currently working on it."
                )
                if not testing:
                    self.write({
                        'state': 'failed',
                        'failure_details': traceback.format_exc(),
                        'answer': sms_answer
                    })
        if 'test' not in sms_text:
            self.env['sms.sender.wizard'].create({
                'text': sms_answer,
                'sms_provider_id': self.env.ref('sms_939.small_account_id').id
            }).send_sms(mobile=sms_receipient)
        else:
            # Test mode will only print url in job return value
            logger.info(
                f"Test service - answer to {sms_receipient}: {sms_answer}")
            return True

    def sponsor_service_fr(self):
        return self.with_context(lang=self.language).sponsor_service()

    def sponsor_service_de(self):
        return self.with_context(lang=self.language).sponsor_service()

    def sponsor_service_it(self):
        return self.with_context(lang=self.language).sponsor_service()

    def sponsor_service(self):
        self.ensure_one()
        # Create a sms child request
        child_request = self.env['sms.child.request'].create({
            'sender': self.sender,
            'lang_code': self.language
        })
        return _(
            "Thank you for your will to help a child ! \n"
            "You can release a child from poverty today by clicking on "
            f"this link: {child_request.full_url}")

    def test_service(self):
        self.ensure_one()
        return "Thanks!"

    def test_service_error(self):
        raise Exception

    @job(default_channel='root')
    def send_sms_answer(self, parameters):
        """Job for sending the SMS reply to a SMS child request.
        :param parameters: SMS parameters received from 939 API.
        :return: True
        """
        sms = self.create({
            'instance': parameters.get('instance'),
            'sender': parameters.get('sender'),
            'operator': parameters.get('operator'),
            'service': parameters.get('service'),
            'language': parameters.get('language'),
            'date': parameters.get('receptionDate'),
            'uuid': parameters.get('requestUid'),
            'text': parameters.get('text'),
        })
        sms.run_service()
