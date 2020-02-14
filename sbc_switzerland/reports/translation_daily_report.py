##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel  Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from odoo import tools
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

try:
    from wand.image import Image as WandImage
except ImportError:
    _logger.warning('Please wand to use SBC module')


class TranslationDailyReport(models.Model):
    _name = "translation.daily.report"
    _table = "translation_daily_report"
    _description = "Daily translations report"
    _rec_name = "correspondence_id"
    _auto = False
    _order = "study_date asc"

    study_date = fields.Char(readonly=True)
    translator_id = fields.Many2one('res.partner', 'Translator', readonly=True)
    ref = fields.Char(related='translator_id.ref')
    name = fields.Char(related='translator_id.name')
    src_lang = fields.Many2one(
        'res.lang.compassion', 'Source language', readonly=True)
    dst_lang = fields.Many2one(
        'res.lang.compassion', 'Destination language', readonly=True)
    language = fields.Char(readonly=True)
    correspondence_id = fields.Many2one(
        'correspondence', 'Letter', readonly=True)
    letter_image = fields.Binary(compute='_compute_letter_image')
    direction = fields.Char(readonly=True)
    translated_text = fields.Text(compute='_compute_translated_text')
    translate_date = fields.Datetime()
    sponsorship_id = fields.Many2one(
        'recurring.contract', 'Sponsorship', readonly=True
    )
    field_office_id = fields.Many2one(
        'compassion.field.office', 'Field office',
        related='sponsorship_id.project_id.field_office_id'
    )
    sponsor = fields.Char(
        'Sponsor', related='sponsorship_id.correspondent_id.name')

    @api.multi
    def _compute_translated_text(self):
        for report in self:
            report.translated_text =\
                report.correspondence_id.translated_text or \
                report.correspondence_id.english_text or \
                report.correspondence_id.original_text

    @api.multi
    def _compute_letter_image(self):
        for report in self.filtered('correspondence_id'):
            pdf = self.correspondence_id.get_image()
            if pdf:
                with WandImage(blob=pdf, resolution=75) as letter_image:
                    report.letter_image = letter_image.make_blob('jpg')\
                        .encode('base64')

    def _date_format(self):
        """
         Used to aggregate data in various formats (in subclasses) "
        :return: (date_trunc value, date format)
        """""
        return 'day', 'YYYY.MM.DD'

    @api.model_cr
    def init(self):
        """
        This SQL view is returning useful statistics about sponsorships.
        The outer query is using window functions to compute cumulative numbers
        Each inner query is computing sum of numbers grouped by _date_format
        :return: None
        """
        tools.drop_view_if_exists(
            self.env.cr, self._table)
        date_format = self._date_format()
        # We disable the check for SQL injection. The only risk of sql
        # injection is from 'self._table' which is not controlled by an
        # external source.
        # pylint:disable=E8103
        self.env.cr.execute(("""
            CREATE OR REPLACE VIEW %s AS
            """ % self._table + """
            -- Super query making windows over monthly data, for cumulative
            -- numbers
            -- http://www.postgresqltutorial.com/postgresql-window-function/
            SELECT
              c.id, c.translator_id, c.src_translation_lang_id AS src_lang,
              c.translation_language_id AS dst_lang,
              l1.name || ' to ' || l2.name AS language,
              to_char(date_trunc(%s, c.translate_date), %s) AS study_date,
              c.sponsorship_id, c.id AS correspondence_id, c.direction,
              c.translate_date
            FROM correspondence c
            JOIN res_lang_compassion l1 ON c.src_translation_lang_id = l1.id
            JOIN res_lang_compassion l2 ON c.translation_language_id = l2.id
            WHERE translator_id IS NOT NULL
        """), date_format)
