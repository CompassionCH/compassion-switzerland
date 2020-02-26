##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields, api


class SportDiscipline(models.Model):
    _name = "sport.discipline"
    _description = "Sport Discipline"

    name = fields.Char(required=True)
    sport = fields.Char(required=True, translate=True)
    distance = fields.Integer(string='Distance (m)', required=True)
    distance_km = fields.Integer(compute='_compute_distance_km')
    page_title = fields.Char(
        translate=True, default='I will go ... for Compassion')

    @api.multi
    @api.depends('distance')
    def _compute_distance_km(self):
        for sport in self:
            sport.distance_km = sport.distance/1000
