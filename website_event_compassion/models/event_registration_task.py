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
    _name = 'event.registration.task'
    _description = 'Event registration task'
    _order = 'sequence, name, id'

    name = fields.Char('Task', required=True, translate=True)
    sequence = fields.Integer(default=1,
                              help="Used to order tasks. Lower is better.")
    stage_id = fields.Many2one(
        'event.registration.stage', 'Stage', required=True,
        help='Associate this task to this registration stage.')
