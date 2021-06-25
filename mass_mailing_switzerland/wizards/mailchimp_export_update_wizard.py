##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields, _
from odoo.exceptions import UserError


class ExportMailchimpWizard(models.TransientModel):
    _inherit = "partner.export.mailchimp"

    @api.multi
    def get_mailing_contact_id(self, partner_id, force_create=False):
        # Avoid exporting opt_out partner
        if force_create:
            partner = self.env["res.partner"].browse(partner_id)
            if partner.opt_out:
                return False
        # Push the partner_id in mailing_contact creation
        return super(
            ExportMailchimpWizard, self.with_context(default_partner_id=partner_id)
        ).get_mailing_contact_id(partner_id, force_create)
