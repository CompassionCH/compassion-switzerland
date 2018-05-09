# -*- coding: utf-8 -*-
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
    _description = "Represent the different discipline one athlete can " \
                   "practice."

    name = fields.Char(required=True)
    sport = fields.Char(required=True)
    distance = fields.Integer(string='Distance (m)', required=True)

    def get_label(self):
        return self.sport.capitalize() + "for" + str(self.distance / 1000) +\
               "km"
