##############################################################################
#
#    Copyright (C) 2018-2022 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel  Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from psycopg2 import sql

from odoo import fields, models, tools

_logger = logging.getLogger(__name__)


class TranslationDailyReport(models.Model):
    _name = "translation.daily.report"
    _table = "translation_daily_report"
    _description = "Daily translations report"
    _rec_name = "correspondence_id"
    _auto = False
    _order = "study_date asc"

    study_date = fields.Char(readonly=True)
    new_translator_id = fields.Many2one("translation.user", "Translator", readonly=True)
    translator_id = fields.Many2one(
        "res.partner", related="new_translator_id.partner_id"
    )
    ref = fields.Char(related="translator_id.ref")
    name = fields.Char(related="translator_id.name")
    src_lang = fields.Many2one("res.lang.compassion", "Source language", readonly=True)
    dst_lang = fields.Many2one(
        "res.lang.compassion", "Destination language", readonly=True
    )
    language = fields.Char(readonly=True)
    correspondence_id = fields.Many2one("correspondence", "Letter", readonly=True)
    letter_image = fields.Binary(compute="_compute_letter_image")
    direction = fields.Char(readonly=True)
    translated_text = fields.Text(compute="_compute_translated_text")
    translate_date = fields.Datetime()
    sponsorship_id = fields.Many2one("recurring.contract", "Sponsorship", readonly=True)
    field_office_id = fields.Many2one(
        "compassion.field.office",
        "Field office",
        related="sponsorship_id.project_id.field_office_id",
        readonly=False,
    )
    sponsor = fields.Char("Sponsor", related="sponsorship_id.correspondent_id.name")

    def _compute_translated_text(self):
        for report in self:
            report.translated_text = (
                report.correspondence_id.translated_text
                or report.correspondence_id.english_text
                or report.correspondence_id.original_text
            )

    def _compute_letter_image(self):
        for report in self.filtered("correspondence_id"):
            report.letter_image = report.correspondence_id.page_ids[0].final_page_image

    def _date_format(self):
        """
         Used to aggregate data in various formats (in subclasses) "
        :return: (date_trunc value, date format)
        """ ""
        return "day", "YYYY.MM.DD"

    def init(self):
        """
        This SQL view is returning useful statistics about sponsorships.
        The outer query is using window functions to compute cumulative numbers
        Each inner query is computing sum of numbers grouped by _date_format
        :return: None
        """
        tools.drop_view_if_exists(self.env.cr, self._table)
        date_trunc_value, date_output_format = self._date_format()

        query = sql.SQL(
            """
            CREATE OR REPLACE VIEW {table} AS
            -- Super query making windows over monthly data, for cumulative
            -- numbers
            -- http://www.postgresqltutorial.com/postgresql-window-function/
            SELECT c.id,
                   c.new_translator_id,
                   c.src_translation_lang_id AS src_lang,
                   c.translation_language_id AS dst_lang,
                   (l1.name->>'en_US')::text || ' to '
                       || (l2.name->>'en_US')::text AS language,
                   to_char(date_trunc({date_trunc}, c.translate_date),
                           {date_format})
                       AS study_date,
                   c.sponsorship_id,
                   c.id AS correspondence_id,
                   c.direction,
                   c.translate_date
            FROM correspondence c
                     JOIN res_lang_compassion l1 ON c.src_translation_lang_id = l1.id
                     JOIN res_lang_compassion l2 ON c.translation_language_id = l2.id
            WHERE new_translator_id IS NOT NULL
            """
        ).format(
            table=sql.Identifier(self._table),
            date_trunc=sql.Literal(date_trunc_value),
            date_format=sql.Literal(date_output_format),
        )
        self.env.cr.execute(query)
