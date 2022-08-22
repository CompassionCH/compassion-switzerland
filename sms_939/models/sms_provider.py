##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields


class SmsProvider(models.Model):
    _name = "sms.provider"
    _description = "SMS Provider"

    name = fields.Char("Configuration name", required=True)
    server_939 = fields.Char("Provider server", required=True)
    port_939 = fields.Integer("Server port", required=True)
    endpoint_939 = fields.Char("Endpoint", required=True)
    username_939 = fields.Char("Username for login", required=True)
    password_939 = fields.Char("Password for login", required=True)
    max_sms_amount = fields.Integer(
        default=5,
        help="Maximum nb. of SMS used for a single sending. Increasing the number may higher the sending costs while "
             "lowering it may result in truncated sendings.")

