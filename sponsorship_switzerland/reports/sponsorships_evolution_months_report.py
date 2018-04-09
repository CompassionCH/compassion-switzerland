# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Sebastien Toth <popod@me.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import tools
from odoo import models, fields, api


class SponsorshipsEvolutionMonthsReport(models.Model):
    _name = "sponsorships.evolution_months.report"
    _table = "sponsorships_evolution_months_report"
    _description = "Sponsorships Evolution By Months"
    _auto = False
    _rec_name = 'activation_date'

    activation_date = fields.Char(string="Activation date", readonly=True)
    active_sponsorships = fields.Integer(
        string="Active sponsorships", readonly=True)

    def _date_format(self):
        """
         Used to aggregate data in various formats (in subclasses) "
        :return: (date_trunc value, date format)
        """""
        return 'month', 'YYYY.MM'

    @api.model_cr
    def init(self):
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
            SELECT
              coalesce(sub.activation_date, jq.end_date) AS activation_date,
              ROW_NUMBER() OVER (ORDER BY (SELECT 100)) AS id,
              sum(coalesce(jq.total, 0)) OVER (ORDER BY activation_date)
                AS cumulative_terminated_sponsorships,
              jq.total AS terminated_sponsorships,
              sum(sub.total) OVER (ORDER BY activation_date) -
              sum(coalesce(jq.total, 0)) OVER (ORDER BY activation_date)
                AS active_sponsorships
            FROM (
              SELECT
                to_char(date_trunc(%s, rc.activation_date),
                        %s) AS activation_date,
                count(rc.activation_date) AS total
              FROM recurring_contract AS rc
              WHERE rc.activation_date IS NOT NULL AND rc.child_id IS NOT NULL
              GROUP BY date_trunc(%s, rc.activation_date)
              ORDER BY activation_date
            ) AS sub
            FULL OUTER JOIN (
              SELECT
                to_char(date_trunc(%s, rc.end_date),
                        %s)
                AS end_date, count(rc.end_date) AS total
              FROM recurring_contract AS rc
              WHERE rc.activation_date IS NOT NULL AND rc.end_date IS NOT NULL
                AND rc.child_id IS NOT NULL
              GROUP BY date_trunc(%s, rc.end_date)
              ORDER BY end_date
            ) AS jq ON sub.activation_date = jq.end_date
        """), (date_format[0], date_format[1], date_format[0],
               date_format[0], date_format[1], date_format[0])
        )
