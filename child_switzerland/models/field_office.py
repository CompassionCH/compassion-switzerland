##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Theo Nikles <theo.nikles@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields


class FieldOffice(models.Model):
    _inherit = 'compassion.field.office'

    # General country info field
    country_info_pdf = fields.Binary(
        compute='_compute_country_info_pdf'
    )
    country_info_filename = fields.Char(
        compute='_compute_info_country_filename')

    # French document
    fr_country_info_pdf = fields.Binary(
        string='Country information French',
        attachment=True
    )

    # German document
    de_country_info_pdf = fields.Binary(
        string='Country information German',
        attachment=True
    )

    # Italian document
    it_country_info_pdf = fields.Binary(
        string='Country information Italian',
        attachment=True
    )

    # English document
    en_country_info_pdf = fields.Binary(
        string='Country information English',
        attachment=True
    )

    @api.multi
    def _compute_info_country_filename(self):
        for field_office in self:
            field_office.country_info_filename = "Country info.pdf"

    @api.multi
    def _compute_country_info_pdf(self):
        """ Computes the PDF corresponding to the lang, given in the
        environment. English is the default language. """
        lang = self.env.lang[:2]
        field_name = lang + '_country_info_pdf'
        for field_office in self:
            field_office.country_info_pdf = getattr(
                field_office, field_name, field_office.en_country_info_pdf)
