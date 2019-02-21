# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Christopher Meier <dev@c-meier.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models


class MatchPartner(models.AbstractModel):
    """
    Extend the matching so that all create partner must be checked by a human.
    """
    _inherit = 'res.partner.match'

    def match_process_create_infos(self, infos):
        create_infos = super(MatchPartner, self).match_process_create_infos(
            infos
        )

        # Mark the partner to be validated
        create_infos['state'] = 'pending'

        return create_infos
