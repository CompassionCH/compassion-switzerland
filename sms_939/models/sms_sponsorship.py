# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Théo Nikles <theo.nikles@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields


class SponsorshipSMS(models.Model):
    _name = 'sms_sponsorship'

    partner_id = fields.Id(string='partner_id')
    text = fields.Char(string='text')
    subject = fields.Text(string='subject')
    date = fields.Datetime(string='date')
