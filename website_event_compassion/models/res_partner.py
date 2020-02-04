##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    registration_ids = fields.One2many(
        'event.registration', 'partner_id', 'Event registrations')
