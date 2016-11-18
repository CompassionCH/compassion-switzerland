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
from openerp import api, models


class CompassionHold(models.Model):
    """ Send Communication when Hold Removal is received. """
    _inherit = 'compassion.hold'

    @api.model
    def beneficiary_hold_removal(self, commkit_data):
        ids = super(CompassionHold, self).beneficiary_hold_removal(
            commkit_data)
        for hold in self.browse(ids).filtered(
                lambda h: h.channel in ('ambassador', 'event')):
            communication_type = self.env.ref(
                'sponsorship_switzerland.hold_removal')
            self.env['partner.communication.job'].create({
                'config_id': communication_type.id,
                'partner_id': hold.primary_owner.partner_id.id,
                'object_id': hold.id,
            })
        return ids
