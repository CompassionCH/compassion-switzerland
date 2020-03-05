##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, api, fields

import re


class MailTrackingEvent(models.Model):
    _inherit = "mail.tracking.event"

    partner_category_ids = fields.Many2many(
        'res.partner.category',
        related='tracking_email_id.partner_id.category_id'
    )

    @api.model
    def create(self, data):
        result = super().create(data)

        if result.url:
            p = re.compile(r'\/([a-zA-Z0-9]{3,6})')
            code = p.findall(result.url)[-1]

            link = self.env['link.tracker.code'].search([('code', '=', code)])

            result.url = link.link_id.url

        return result
