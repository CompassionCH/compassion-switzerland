##############################################################################
#
#    Copyright (C) 2017-2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, api


class CorrespondenceMetadata(models.AbstractModel):
    """ Add mailing origin in correspondence objects. """
    _inherit = ['correspondence.metadata', 'utm.mixin']
    _name = 'correspondence.metadata'

    @api.model
    def get_fields(self):
        res = super().get_fields()
        res.extend(['campaign_id', 'source_id', 'medium_id'])
        return res

    @api.multi
    def get_correspondence_metadata(self):
        vals = super().get_correspondence_metadata()
        if vals.get('campaign_id'):
            vals['campaign_id'] = vals['campaign_id'][0]
        if vals.get('source_id'):
            vals['source_id'] = vals['source_id'][0]
        if vals.get('medium_id'):
            vals['medium_id'] = vals['medium_id'][0]
        return vals
