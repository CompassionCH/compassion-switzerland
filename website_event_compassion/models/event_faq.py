##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields


class EventFaqCategory(models.Model):
    _name = 'event.faq.category'
    _description = 'Event FAQ Category'
    _order = 'sequence asc,name asc'

    name = fields.Char('Category name', required=True, translate=True)
    sequence = fields.Integer(default=1)
    event_type_ids = fields.Many2many(
        'event.type', string='Applies to',
        help='Leave empty to make the category appear on all events'
    )
    question_ids = fields.One2many('event.faq', 'category_id', 'Questions')


class EventFaq(models.Model):
    _name = 'event.faq'
    _description = 'Event FAQ'
    _rec_name = 'question_title'
    _order = 'sequence asc,question_title asc'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    question_title = fields.Char(required=True, translate=True)
    category_id = fields.Many2one(
        'event.faq.category', 'Category', required=True)
    question_answer = fields.Html(required=True, translate=True)
    sequence = fields.Integer()
    event_type_ids = fields.Many2many(
        'event.type', string='Applies to',
        help='Leave empty to make the question appear on all events'
    )
