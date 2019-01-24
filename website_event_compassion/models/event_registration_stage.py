# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields


class EventStage(models.Model):
    _name = 'event.registration.stage'
    _description = 'Event registration stage'
    _order = 'sequence, name, id'

    name = fields.Char('Stage name', required=True, translate=True)
    sequence = fields.Integer(default=1,
                              help="Used to order stages. Lower is better.")
    duration = fields.Integer(
        help="Set a maximum duration (in days) after which the registration "
             "will be shown in red in the kanban view.")
    requirements = fields.Text(
        'Requirements',
        help="Enter here the internal requirements for this stage"
             "(ex: Sign contract). It will appear as a tooltip over "
             "the stage's name.")
    event_type_ids = fields.Many2many(
        'event.type', 'event_registration_stage_to_type_rel',
        string='Event types', ondelete='set null',
        help='Specific event types that use this stage. '
             'Other event types will not be able to see or use this stage.')
    fold = fields.Boolean(
        'Folded in Pipeline',
        help='This stage is folded in the kanban view when there are no '
             'records in that stage to display.')
