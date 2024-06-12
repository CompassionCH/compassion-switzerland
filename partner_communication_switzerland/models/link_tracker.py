##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#    @author: Jérémie Lang <jlang@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from werkzeug import urls

from odoo import models


class LinkTracker(models.Model):
    _inherit = "link.tracker"

    def _compute_short_url_host(self):
        for tracker in self:
            base_url = (self.env["ir.config_parameter"]
                        .sudo().get_param("web.external.url"))
            tracker.short_url_host = urls.url_join(base_url, '/r/')
