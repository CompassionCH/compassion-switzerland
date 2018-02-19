# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models


class SubSponsorshipWizard(models.TransientModel):
    _inherit = "sds.subsponsorship.wizard"

    @api.multi
    def create_subsponsorship(self):
        res = super(SubSponsorshipWizard, self).create_subsponsorship()
        if self.child_id:
            # In this case the sponsorship is already made
            # we generate the departure letter.
            sponsorship_id = self.env.context.get('active_id')
            sponsorship = self.env['recurring.contract'].browse(sponsorship_id)
            res = self.send_sub_communication(sponsorship, True) or res
        return res

    @api.multi
    def no_sub(self):
        """ No SUB for the sponsorship. """
        res = super(SubSponsorshipWizard, self).no_sub()
        sponsorship_id = self.env.context.get('active_id')
        contract = self.env['recurring.contract'].browse(sponsorship_id)
        res = self.send_sub_communication(contract, False) or res
        return res

    @api.model
    def send_sub_communication(self, sponsorship, sub_proposal):
        """
        Selects and send the correct communication after making sub sponsorship
        :param sponsorship: recurring.contract record
        :param sub_proposal: True if we send a sub sponsorship, or False if
                             we are making a No Sub.
        :return: Action for opening generated communication or False if no
                 communication was generated
        """
        config = False
        res = False
        if sponsorship.state != 'active':
            # Generate depart letter
            child = sponsorship.child_id
            lifecycle_type = (
                child.lifecycle_ids and child.lifecycle_ids[0].type
            ) or 'Unplanned Exit'
            if lifecycle_type == 'Planned Exit':
                config = self.env.ref(
                    'partner_communication_switzerland.'
                    'lifecycle_child_planned_exit'
                )
            elif lifecycle_type == 'Unplanned Exit':
                config = self.env.ref(
                    'partner_communication_switzerland.'
                    'lifecycle_child_unplanned_exit'
                )
                if child.lifecycle_ids[0].request_reason == 'deceased':
                    sponsorship = sponsorship.with_context(
                        default_need_call=True)
        else:
            # In case of No SUB, the contract can still be active.
            # Contract is active -> generate no sub confirmation
            config = self.env.ref(
                'partner_communication_switzerland.planned_no_sub')

        if config:
            communications = sponsorship.send_communication(
                config, correspondent=False)
            res = {
                'name': communications[0].subject,
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'partner.communication.job',
                'domain': [('id', 'in', communications.ids)],
                'target': 'current',
                'context': self.env.context
            }
        return res
