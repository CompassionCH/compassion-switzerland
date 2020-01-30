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


from odoo import models, api, fields, _
from odoo.exceptions import ValidationError


logger = logging.getLogger(__name__)


class SmsHook(models.Model):
    """ A sponsored child """
    _name = 'sms.hook'
    _description = 'SMS Keyword Hook'

    name = fields.Char(
        'Keyword service',
        help='This hook will be called when a SMS from this registered'
             'service is received.',
        required=True
    )
    func_name = fields.Char(
        'Function',
        help='Method name that will be executed at reception. The method must '
        'exist in sms.notification object and returns a '
        'SmsNotificationAnswer object',
        required=True
    )

    @api.constrains('func_name')
    def check_func_name(self):
        if not hasattr(self.env['sms.notification'], self.__name__):
            raise ValidationError(
                _("The function is not implemented in sms.notification"))
