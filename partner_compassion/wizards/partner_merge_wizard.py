
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, _
from odoo.exceptions import UserError


class PartnerMergeWizard(models.TransientModel):
    _inherit = 'base.partner.merge.automatic.wizard'

    @api.multi
    def action_merge(self):
        """
        - Allow anybody to perform the merge of partners
        - Prevent geoengine bugs
        - Prevent to merge sponsors
        - Save other e-mail addresses in linked partners
        """
        removing = self.partner_ids - self.dst_partner_id
        geo_point = self.dst_partner_id.geo_point
        self.partner_ids.write({'geo_point': False})
        sponsorships = self.env['recurring.contract'].search([
            ('correspondent_id', 'in', removing.ids),
            ('state', '=', 'active'),
            ('type', 'like', 'S')
        ])
        if sponsorships:
            raise UserError(_(
                "The selected partners are sponsors! "
                "Please first modify the sponsorship and don't forget "
                "to send new labels to them."
            ))
        old_emails = removing.filtered('email').mapped('email')
        new_email = self.dst_partner_id.email
        for email in old_emails:
            if new_email and email != new_email:
                self.dst_partner_id.copy({
                    'contact_id': self.dst_partner_id.id,
                    'email': email,
                    'type': 'email_alias'
                })
        res = super(self.sudo()).action_merge()
        self.dst_partner_id.geo_point = geo_point
        return res
