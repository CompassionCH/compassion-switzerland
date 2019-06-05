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

from odoo import api, models, fields
from odoo.exceptions import ValidationError


class FieldOffice(models.Model):
    _inherit = 'compassion.field.office'

    country_info_pdf = fields.Binary(string='Data Pdf', filters='*.pdf')
    filename = fields.Char(string='File Name')
