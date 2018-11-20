# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#    @author: Sebastien Toth <popod@me.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    muskathlon_participant_id = fields.Char('Muskathlon participant ID')


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def signup(self, values, token=None):
        """ Mark acccount activation task done for Muskathlon participant. """
        res = super(ResUsers, self).signup(values, token)
        login = res[1]
        user = self.env['res.users'].search([('login', '=', login)])
        registration = user.partner_id.registration_ids[:1]
        if registration.event_id.event_type_id == self.env.ref(
                'muskathlon.event_type_muskathlon'):
            registration.write({'completed_task_ids': [
                (4, self.env.ref('muskathlon.task_activate_account').id)
            ]})
        return res
