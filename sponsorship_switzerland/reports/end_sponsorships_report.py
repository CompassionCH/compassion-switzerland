# -*- coding: utf-8 -*-

from odoo import api, models, fields, tools


class EndSponsorshipsMonthReport(models.Model):
    _name = "end.sponsorships.month.report"
    _inherit = "fiscal.year.report"
    _table = 'end_sponsorships_month_report'
    _description = "End of sponsorships monthly report"
    _auto = False
    _rec_name = 'end_date'

    end_date = fields.Datetime(readonly=True)
    sub_sponsorship_id = fields.Many2one('recurring.contract', readonly=True)
    category = fields.Selection([
        ('child', 'Child departure'),
        ('sponsor', 'Sponsor end')
    ], readonly=True)
    sub_category = fields.Selection([
        ('sub', 'Sub'),
        ('no_sub', 'No sub')
    ], readonly=True)
    end_reason = fields.Selection('get_ending_reasons', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)
    lang = fields.Selection('select_lang', readonly=True)
    sds_state = fields.Selection('_get_sds_states', readonly=True)
    active_percentage = fields.Float(
        string='Percentage (/active)',
        help='Percentage on active sponsorships in that period',
        readonly=True)
    total_percentage = fields.Float(
        string='Percentage (/terminated)',
        help='Percentage on total ended sponsorships in that period',
        readonly=True
    )

    @api.model
    def select_lang(self):
        langs = self.env['res.lang'].search([])
        return [(lang.code, lang.name) for lang in langs]

    def get_ending_reasons(self):
        return self.env['recurring.contract'].with_context(
            default_type='S').get_ending_reasons()

    def _get_sds_states(self):
        return self.env['recurring.contract']._get_sds_states()

    def _select_category(self):
        return """
            CASE c.end_reason
            WHEN '1' THEN 'child'
            ELSE 'sponsor'
            END
            AS category
        """

    def _select_sub_category(self):
        return """
            CASE c.sds_state
            WHEN 'sub' THEN 'sub'
            WHEN 'sub_accept' THEN 'sub'
            ELSE 'no_sub'
            END
            AS sub_category
        """

    def _join_stats(self):
        """ Useful to compare against number active sponsorships in the
        period. """
        return """
            JOIN sponsorships_evolution_months_report s
            ON to_char(c.end_date, 'YYYY.MM') = s.activation_date
        """

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        # We disable the check for SQL injection. The only risk of sql
        # injection is from 'self._table' which is not controlled by an
        # external source.
        # pylint:disable=E8103
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS
            SELECT c.id, c.end_date, c.end_reason, c.sub_sponsorship_id,
                   c.sds_state, p.id as partner_id, %s, %s, %s,
                   p.lang, 100/s.active_sponsorships as active_percentage,
                   100.0/s.terminated_sponsorships as total_percentage,
                   s.terminated_sponsorships,
                   s.activation_date
            FROM recurring_contract c JOIN res_partner p
              ON c.correspondant_id = p.id
              %s
            WHERE c.state = 'terminated' AND c.child_id IS NOT NULL
            AND c.end_date IS NOT NULL
        """ % (self._table,
               self._select_fiscal_year('c.end_date'),
               self._select_category(),
               self._select_sub_category(),
               self._join_stats())
        )
