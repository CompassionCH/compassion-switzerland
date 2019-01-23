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


class Muskathlon(models.Model):
    _name = "muskathlon.report"
    _description = "Muskathlon report"
    _auto = False
    _table = "muskathlon_report"
    _order = "event_id asc,date desc"

    # fields needed for display in tree view
    # WARNING: do not change fields name (used in csv export file)
    date_display = fields.Date(readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)
    partner_name = fields.Char(related="partner_id.display_name",
                               readonly=True)
    user_id = fields.Many2one('res.partner', "Ambassador", readonly=True)
    amount = fields.Float("Amount", readonly=True)
    amount_cent = fields.Integer("Amount in currency (cents)", readonly=True)
    sent_to_4m = fields.Date("Date sent to 4M", readonly=True)
    payment_mode_id = fields.Many2one('account.payment.mode', "Payment mode",
                                      readonly=True)
    event_id = fields.Many2one('crm.event.compassion', "Event", readonly=True)
    journal_id = fields.Many2one('account.journal', 'Journal', readonly=True)

    # fields needed for csv exportation
    # we cannot use relation fields define before due to csv exportation..
    # WARNING: do not change fields name (used in csv export file)
    status = fields.Char(string="Status", readonly=True)
    type = fields.Char(string="Type", readonly=True)
    payment_method = fields.Char("Paymentmethod", readonly=True,
                                 oldname="payment_methode")
    project_id = fields.Char("ProjectID", readonly=True)
    date = fields.Datetime("Date/time", readonly=True)
    muskathlon_participant_id = fields.Char("ParticipantID", readonly=True)
    registration_id = fields.Char('RegistrationID', readonly=True)
    sponsorship_name = fields.Char("Sponsorship name", readonly=True)

    # Fields for viewing related objects
    contract_id = fields.Many2one('recurring.contract', 'Sponsorship',
                                  readonly=True)
    invoice_line_id = fields.Many2one('account.invoice.line', 'Invoice line',
                                      readonly=True)
    donation_type = fields.Selection(
        [('sponsorship', 'Sponsorship'),
         ('donation', 'Donation')], compute='_compute_donation_type')

    @api.multi
    def _compute_donation_type(self):
        for line in self:
            line.donation_type = 'donation' if line.invoice_line_id else \
                'sponsorship'

    @api.model_cr
    def init(self):
        # to prevent IDs duplication with UNION, recurring contracts IDs are
        # pair and account invoice IDs are impair.
        # many fields are hardcoded due to csv exportation needs
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
              SELECT
                (2 * ROW_NUMBER() OVER (ORDER BY (SELECT rc.id))) AS id,
                rc.id AS contract_id,
                NULL AS invoice_line_id,
                rc.partner_id,
                rc.user_id,
                1000 AS amount,
                100000 AS amount_cent,
                rc.sent_to_4m,
                rc.payment_mode_id,
                rco.event_id,
                NULL AS journal_id,
                rp.muskathlon_participant_id,
                rp2.name AS sponsorship_name,
                rc.start_date AS date,
                rc.start_date AS date_display,
                'success' AS status,
                'sponsor' AS type,
                'transfer' AS payment_method,
                cec.muskathlon_event_id AS project_id,
                mr.reg_id AS registration_id
              FROM recurring_contract AS rc
              LEFT JOIN res_partner AS rp ON rp.id = rc.user_id
              LEFT JOIN res_partner AS rp2 ON rc.partner_id = rp2.id
              LEFT JOIN recurring_contract_origin AS rco
                ON rc.origin_id = rco.id
              LEFT JOIN crm_event_compassion AS cec ON rco.event_id = cec.id
              LEFT JOIN event_registration mr ON rp.id = mr.partner_id
              WHERE cec.muskathlon_event_id IS NOT NULL
            )
            UNION ALL (
              SELECT
                (2 * ROW_NUMBER() OVER (ORDER BY (SELECT ail.id)) - 1) AS id,
                NULL AS contract_line_id,
                ail.id AS invoice_line_id,
                ail.partner_id,
                ail.user_id,
                aml.credit AS amount,
                aml.credit * 100 AS amount_cent,
                ail.sent_to_4m,
                ai.payment_mode_id,
                ail.event_id,
                aml.journal_id AS journal_id,
                rp.muskathlon_participant_id,
                rp2.name AS sponsorship_name,
                ai.date_invoice AS date,
                ai.date_invoice AS date_display,
                'success' AS status,
                'sponsor' AS type,
                'transfer' AS payment_method,
                cec.muskathlon_event_id AS project_id,
                mr.reg_id AS registration_id
              FROM account_invoice_line AS ail
              LEFT JOIN account_invoice AS ai ON ail.invoice_id = ai.id
              LEFT JOIN account_move AS am ON ai.move_id = am.id
                AND ai.partner_id = am.partner_id
              INNER JOIN LATERAL
                (SELECT *
                FROM account_move_line
                WHERE move_id = am.id
                AND credit > 0
                FETCH FIRST 1 ROW ONLY
                ) aml ON TRUE
              LEFT JOIN res_partner AS rp ON rp.id = ail.user_id
              LEFT JOIN res_partner AS rp2 ON ail.partner_id = rp2.id
              LEFT JOIN crm_event_compassion AS cec ON ail.event_id = cec.id
              LEFT JOIN event_registration AS mr
                ON mr.partner_id = rp.id AND mr.event_id = cec.odoo_event_id
              WHERE ail.state IN ('draft', 'open', 'paid')
                AND ail.account_id = 2775
                AND cec.muskathlon_event_id IS NOT NULL
                AND ail.user_id IS NOT NULL
            )
        """ % self._table)

    @api.multi
    def send_to_4m(self):
        self.mapped('contract_id').write({'sent_to_4m': fields.Date.today()})
        self.mapped('invoice_line_id').write({
            'sent_to_4m': fields.Date.today()})
