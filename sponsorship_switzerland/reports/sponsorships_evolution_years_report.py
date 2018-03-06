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


class SponsorshipsEvolutionYearsReport(models.Model):
    _name = "sponsorships.evolution_years.report"
    _description = "Sponsorships Evolution By Years"
    _auto = False
    _rec_name = 'activation_date'

    activation_date = fields.Char(string="Activation date", readonly=True)
    active_sponsorships = fields.Integer(string="Active sponsorships",
                                             readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr,
                                  'sponsorships_evolution_years_report')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW sponsorships_evolution_years_report AS
            SELECT
              coalesce(sub.activation_date, jq.end_date) AS activation_date,
              ROW_NUMBER() OVER (ORDER BY (SELECT 100)) AS id,
              sum(coalesce(jq.total, 0)) OVER (ORDER BY activation_date)
                AS terminated_sponsorships,
              sum(sub.total) OVER (ORDER BY activation_date) -
              sum(coalesce(jq.total, 0)) OVER (ORDER BY activation_date)
                AS active_sponsorships
            FROM (
              SELECT
                to_char(date_trunc('year', rc.activation_date), 'YYYY')
                AS activation_date, count(rc.activation_date) AS total
              FROM recurring_contract AS rc
              WHERE rc.activation_date IS NOT NULL AND rc.child_id IS NOT NULL
              GROUP BY date_trunc('year', rc.activation_date)
              ORDER BY activation_date
            ) AS sub
            FULL OUTER JOIN (
              SELECT
                to_char(date_trunc('year', rc.end_date), 'YYYY')
                AS end_date, count(rc.end_date) AS total
              FROM recurring_contract AS rc
              WHERE rc.activation_date IS NOT NULL AND rc.end_date IS NOT NULL
                AND rc.child_id IS NOT NULL
              GROUP BY date_trunc('year', rc.end_date)
              ORDER BY end_date
            ) AS jq ON sub.activation_date = jq.end_date
        """)
