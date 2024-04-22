##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, api
from urllib.parse import urljoin

class LinkTracker(models.Model):
    _inherit = 'link.tracker'

    # Ensure this field definition matches the one in Odoo 14 link.tracker model
    short_url = fields.Char(compute='_compute_short_url', store=True)

    @api.depends('code')
    def _compute_short_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.external.url')
        for link in self:
            link.short_url = urljoin(base_url, "/r/%s" % link.code)

