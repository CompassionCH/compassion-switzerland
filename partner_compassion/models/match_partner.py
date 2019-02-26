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

    def match_after_match(self, partner, new_partner, infos):
        """
        Activate partner if it was a linked contact.
        :param partner: res.partner record matched
        :param new_partner: True if a new partner was created
        :param infos: partner infos extracted from form
        :return: None
        """
        if partner.contact_type == 'attached':
            if partner.type == 'email_alias':
                # In this case we want to link to the main partner
                partner = partner.contact_id
                # Don't update e-mail address of main partner
                del infos['email']
            else:
                # We unarchive the partner to make it visible
                partner.write({
                    'active': True,
                    'contact_id': False
                })
        return super(MatchPartner, self).match_after_match(
            partner, new_partner, infos
        )
