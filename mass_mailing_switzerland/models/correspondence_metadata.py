# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from odoo import models, api, fields


class CorrespondenceMetadata(models.AbstractModel):
    """ Add mailing origin in correspondence objects. """
    _inherit = 'correspondence.metadata'

    mailing_campaign_id = fields.Many2one('mail.mass_mailing.campaign')

    @api.model
    def get_fields(self):
        res = super(CorrespondenceMetadata, self).get_fields()
        res.append('mailing_campaign_id')
        return res

    @api.multi
    def get_correspondence_metadata(self):
        vals = super(CorrespondenceMetadata,
                     self).get_correspondence_metadata()
        if vals.get('mailing_campaign_id'):
            vals['mailing_campaign_id'] = vals['mailing_campaign_id'][0]
        return vals
