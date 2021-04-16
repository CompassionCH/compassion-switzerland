##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    @author: Théo Nikles <theo.nikles@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields


class MailActivityMixin(models.AbstractModel):
    _inherit = 'mail.activity.mixin'

    activity_ids = fields.One2many(groups=False)
