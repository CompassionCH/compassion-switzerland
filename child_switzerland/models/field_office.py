# -*- coding: utf-8 -*-
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

    # French document
    fr_country_info_pdf = fields.Binary(
        string='Country information French',
        attachment=True
    )
    fr_filename = fields.Char(string='fr_filename')

    # German document
    de_country_info_pdf = fields.Binary(
        string='Country information German',
        attachment=True
    )
    de_filename = fields.Char(string='de_filename')

    # Italian document
    it_country_info_pdf = fields.Binary(
        string='Country information Italian',
        attachment=True
    )
    it_filename = fields.Char(string='it_filename')

    # English document
    en_country_info_pdf = fields.Binary(
        string='Country information English',
        attachment=True
    )
    en_filename = fields.Char(string='en_filename')

    """ Returns the PDF corresponding to the lang, given as input. Since
    English is the default language, it does not need to be in the table
    since it is the default value of the access """
    @api.multi
    def get_country_info_pdf_lang(self, lang):
        """
        Returns the PDF file description of the country according to the
        provided language. English is returned by default, if there is
        no PDF file for the given language. The method offers file for
        French, Italian, German and English.

        :param lang: the desired language for the PDF file
        :return: the PDF file as a string in base64, in the desired language
        or English, by default
        """
        if lang == 'fr_CH':
            return self.fr_country_info_pdf
        elif lang == 'de_CH':
            return self.de_country_info_pdf
        elif lang == 'it_CH':
            return self.it_country_info_pdf
        else:
            # default case, return English version
            return self.en_country_info_pdf
