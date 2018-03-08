# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields


class EventCompassion(models.Model):
    _inherit = 'crm.event.compassion'

    thank_you_text = fields.Html(translate=True)

    muskathlon_project_id = fields.Char(
        string="Muskathlon project ID", size=128)
    muskathlon_registration_ids = fields.One2many(
        'muskathlon.registration', 'project_id')


class MuskathlonRegistration(models.Model):
    _name = 'muskathlon.registration'

    project_id = fields.Many2one(comodel_name='crm.event.compassion',
                                 string='Muskathlon project')
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Muskathlon participant')

    muskathlon_ambassador_id = fields.Char(
        related='partner_id.muskathlon_ambassador_id')

    muskathlon_project_id = fields.Char(
        related='project_id.muskathlon_project_id')

    reg_id = fields.Char(string='Muskathlon registration ID', size=128)
