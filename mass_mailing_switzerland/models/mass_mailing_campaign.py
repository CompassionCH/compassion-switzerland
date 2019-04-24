# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016-2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields

from odoo.addons.queue_job.job import job, related_action


class MassMailingCampaign(models.Model):
    _inherit = 'mail.mass_mailing.campaign'
    _order = 'id desc'

    clicks_ratio = fields.Integer(compute='_compute_click_ratios', store=True)
    unsub_ratio = fields.Integer(compute='_compute_unsub_ratio', store=True)
    contract_ids = fields.One2many(
        'recurring.contract', related='campaign_id.contract_ids'
    )
    correspondence_ids = fields.One2many(
        'correspondence', related='campaign_id.correspondence_ids'
    )
    invoice_line_ids = fields.One2many(
        'account.invoice.line', compute='_compute_campaign_invoices'
    )

    @api.multi
    def _compute_campaign_invoices(self):
        mass_medium = self.env.ref(
            'contract_compassion.utm_medium_mass_mailing')
        for campaign in self:
            campaign.invoice_line_ids = campaign.campaign_id.invoice_line_ids\
                .filtered(lambda invl: invl.medium_id == mass_medium)

    @api.depends('mass_mailing_ids.clicks_ratio')
    def _compute_click_ratios(self):
        for campaign in self:
            total_clicks = 0
            total_sent = len(campaign.mapped(
                'mass_mailing_ids.statistics_ids'))
            for mailing in campaign.mass_mailing_ids:
                total_clicks += (mailing.clicks_ratio / 100.0) * len(
                    mailing.statistics_ids)
            if total_sent:
                campaign.clicks_ratio = (total_clicks / total_sent) * 100

    @api.depends('mass_mailing_ids.unsub_ratio')
    def _compute_unsub_ratio(self):
        for campaign in self:
            total_unsub = 0
            total_sent = len(campaign.mapped(
                'mass_mailing_ids.statistics_ids'))
            for mailing in campaign.mass_mailing_ids:
                total_unsub += (mailing.unsub_ratio / 100.0) * len(
                    mailing.statistics_ids)
            if total_sent:
                campaign.unsub_ratio = (total_unsub / total_sent) * 100

    @api.multi
    def open_unsub(self):
        return self.mass_mailing_ids.open_unsub()

    @api.multi
    def open_clicks(self):
        return self.mass_mailing_ids.open_clicks()


class Mail(models.Model):
    _inherit = 'mail.mail'

    @job(default_channel='root.mass_mailing')
    @related_action(action='related_action_emails')
    @api.multi
    def send_sendgrid_job(self, mass_mailing_ids=False):
        # Make send method callable in a job
        self.send_sendgrid()
        if mass_mailing_ids:
            mass_mailings = self.env['mail.mass_mailing'].browse(
                mass_mailing_ids)
            mass_mailings.write({'state': 'done'})
        return True
