# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields


class AmbassadorDetails(models.Model):
    _name = "ambassador.details"
    _description = "Ambassador Details"
    _rec_name = "partner_id"

    partner_id = fields.Many2one(
        'res.partner', required=True, ondelete='cascade')
    description = fields.Text(translate=True)
    quote = fields.Text(translate=True)
    picture_large = fields.Binary(
        attachment=True, help='Large picture for profile page')
    picture_filename = fields.Char(compute='_compute_filename')
    thank_you_quote = fields.Html(
        help='Used in thank you letters for donations linked to an event '
             'and to this partner.',
    )
    mail_copy_when_donation = fields.Boolean()

    @api.multi
    def _compute_filename(self):
        for details in self:
            partner_name = details.display_name
            details.picture_filename = partner_name + '-large.jpg'
