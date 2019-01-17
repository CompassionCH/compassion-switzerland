# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, _


class ResCountryVaccine(models.Model):
    _name = 'res.country.vaccine'
    _description = 'Country Vaccines'

    name = fields.Char(related='vaccine_id.name')
    country_id = fields.Many2one(
        'res.country', 'Country',
        required=True, ondelete='cascade', index=True)
    vaccine_id = fields.Many2one(
        'res.vaccine', 'Vaccine',
        required=True, ondelete='cascade', index=True)
    mandatory = fields.Boolean(
        help="True if the vaccine is mandatory when travelling to the country"
    )

    _sql_constraints = [
        ('unique_vaccine', 'unique(country_id,vaccine_id)',
         _('This vaccine is already set'))
    ]


class ResVaccine(models.Model):
    _name = 'res.vaccine'
    _description = 'Vaccine'

    name = fields.Char(required=True, translate=True)

    _sql_constraints = [
        ('unique_vaccine', 'unique(name)',
         _('This vaccine already exists'))
    ]


class ResCountry(models.Model):
    _inherit = 'res.country'

    vaccine_ids = fields.One2many(
        'res.country.vaccine', 'country_id', 'Vaccines')
    description_url = fields.Char(translate=True)
