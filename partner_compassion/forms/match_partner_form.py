##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields


class MatchPartnerForm(models.AbstractModel):
    _inherit = "cms.form.match.partner"

    # Restrict allowed titles
    partner_title = fields.Many2one(domain=lambda s: s.public_title_domain())

    def public_title_domain(self):
        titles = (
            self.env.ref("base.res_partner_title_mister") +
            self.env.ref("base.res_partner_title_madam") +
            self.env.ref("partner_compassion.res_partner_title_family")
        )
        return [("id", "in", titles.ids)]
