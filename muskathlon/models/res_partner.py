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
from odoo.addons.queue_job.job import job, related_action


class ResPartner(models.Model):
    _inherit = 'res.partner'

    muskathlon_participant_id = fields.Char('Muskathlon participant ID')
    muskathlon_registration_ids = fields.One2many(
        'muskathlon.registration', 'partner_id', 'Muskathlon registrations')

    @api.multi
    @job(default_channel='root.muskathlon')
    @related_action('related_action_partner')
    def create_ambassador_details(self, details_vals):
        """ Create ambassador details. """
        self.ambassador_details_id = self.ambassador_details_id.create(
            details_vals)
        return True
