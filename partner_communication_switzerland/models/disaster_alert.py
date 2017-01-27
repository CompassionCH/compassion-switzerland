# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from urllib import urlencode
from urlparse import urljoin
from openerp import api, models, fields


class DisasterAlert(models.Model):
    """ Add fields for retrieving values for communications.
    Send a communication when a major revision is received.
    """
    _inherit = 'fo.disaster.alert'

    access_link = fields.Char(compute='_compute_access_link')

    def _compute_access_link(self):
        """Generate URL for disaster alert."""
        for disaster in self:
            base_url = self.env['ir.config_parameter'].get_param(
                'web.base.url')
            query = {'db': self.env.cr.dbname}
            fragment = {
                'view_type': 'form',
                'id': disaster.id,
                'menu_id': self.env.ref(
                    'child_compassion.'
                    'menu_sponsorship_field_office_disaster_alert').id,
                'action': self.env.ref(
                    'child_compassion.'
                    'open_view_field_office_disaster').id,
            }
            action = "/web?%s#%s" % (urlencode(query), urlencode(fragment))
            disaster.access_link = urljoin(base_url, action)

    @api.model
    def create(self, vals):
        disaster = super(DisasterAlert, self).create(vals)
        children = disaster.mapped(
            'child_disaster_impact_ids.child_id').filtered('sponsor_id')
        sponsors = children.mapped('sponsor_id')
        communication_config = self.env.ref(
            'partner_communication_switzerland.disaster_alert')
        job_obj = self.env['partner.communication.job']
        for partner in sponsors:
            sponsorships = partner.sponsorship_ids.filtered(
                lambda s: s.child_id in children)
            job_obj.create({
                'partner_id': partner.id,
                'config_id': communication_config.id,
                'object_ids': sponsorships.ids
            })
        return disaster
