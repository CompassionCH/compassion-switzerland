# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields


class AmbassadorDetails(models.Model):
    _name = "ambassador.details"
    _description = "Additional details about an ambassador"

    partner_id = fields.Many2one('res.partner')
    description = fields.Text(translate=True)
    quote = fields.Text(translate=True)
    picture_1 = fields.Binary(attachment=True)
    picture_2 = fields.Binary(attachment=True)
    thank_you_quote = fields.Html(
        help='Used in thank you letters for donations linked to an event '
             'and to this partner.',
    )
    mail_copy_when_donation = fields.Boolean()
