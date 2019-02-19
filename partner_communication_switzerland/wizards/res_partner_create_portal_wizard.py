# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Joel Vaucher <jvaucher@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


from odoo import api, models, fields, _


class ResPartnerCreatePortalWizard(models.TransientModel):
    """ creation of a portal user wizard will send a email
        with the identifier if the user used the checkbox """
    _name = 'res.partner.create.portal.wizard'
    _description = 'take a partner and make it a odoo user'

    create_communication = fields.Boolean(
        'Send an e-mail invitation', default=True)

    config_id = fields.Many2one(
        'partner.communication.config', 'choose a communication',
        domain="[('model', '=', 'res.users')]",
        default=lambda self: self.env.ref('partner_communication_switzerland'
                                          '.portal_welcome_config').id
    )

    @api.multi
    def button_create_portal_user(self):
        portal = self.env['portal.wizard'].create({
            'invitation_config_id': self.config_id.id
        })
        portal.onchange_portal_id()
        users_portal = portal.mapped('user_ids')
        users_portal.write({'in_portal': True})

        # create a temporary fake email address for partner without email,
        # their accounts have to be activate manually
        no_mail = users_portal.filtered(lambda u: not u.email)
        for user in no_mail:
            partner = user.partner_id
            user.email = partner.firstname[0].lower() + \
                partner.lastname.lower() + '@cs.local'

        portal.with_context({
            'create_communication': self.create_communication
        }).action_apply()

        no_mail.mapped('partner_id').write({'email': False})

        action = True
        if self.create_communication:
            uid_communication = portal.mapped('user_ids.uid_communication_id')
            action = {
                'name': _('Communications'),
                'type': 'ir.actions.act_window',
                'res_model': 'partner.communication.job',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'domain': [('id', 'in', uid_communication.ids)],
                'flags': {'action_buttons': True}
            }
        return action

    @api.multi
    def button_cancel(self):
        return True
