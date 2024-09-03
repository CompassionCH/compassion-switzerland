##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models


class Partner(models.Model):
    _inherit = "res.partner"

    def write(self, vals):
        if "email" in vals:
            for partner in self:
                if not vals["email"] and partner.sudo().mass_mailing_contact_ids:
                    partner.sudo().mass_mailing_contact_ids.unlink()
        return super(Partner, self).write(vals)
