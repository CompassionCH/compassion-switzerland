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
from odoo.addons.website.models.website import slugify
import re


class MassMailingCampaign(models.Model):
    _inherit = 'mail.mass_mailing.campaign'
    _order = 'id desc'

    clicks_ratio = fields.Integer(compute='_compute_ratios', store=True,
                                  oldname='click_ratio')
    unsub_ratio = fields.Integer(compute='_compute_ratios', store=True)
    mailing_origin_id = fields.Many2one(
        'recurring.contract.origin', 'Origin', domain=[('analytic_id', '!=',
                                                        False)])
    mailing_slug = fields.Char()
    contract_ids = fields.One2many(
        'recurring.contract', 'mailing_campaign_id', 'Sponsorships',
        readonly=True
    )
    correspondence_ids = fields.One2many(
        'correspondence', 'mailing_campaign_id', 'Sponsor letters',
        readonly=True
    )
    invoice_ids = fields.One2many(
        'account.invoice', 'mailing_campaign_id', 'Donations', readonly=True
    )

    @api.depends('mass_mailing_ids.clicks_ratio',
                 'mass_mailing_ids.unsub_ratio')
    def _compute_ratios(self):
        for campaign in self:
            total_clicks = 0
            total_unsub = 0
            total_sent = len(campaign.mapped(
                'mass_mailing_ids.statistics_ids'))
            for mailing in campaign.mass_mailing_ids:
                total_clicks += (mailing.clicks_ratio / 100.0) * len(
                    mailing.statistics_ids)
                total_unsub += (mailing.unsub_ratio / 100.0) * len(
                    mailing.statistics_ids)
            if total_sent:
                campaign.clicks_ratio = (total_clicks / total_sent) * 100
                campaign.unsub_ratio = (total_unsub / total_sent) * 100

    @api.multi
    def open_unsub(self):
        return self.mass_mailing_ids.open_unsub()

    @api.multi
    def open_clicks(self):
        return self.mass_mailing_ids.open_clicks()

    @api.onchange('mailing_origin_id')
    def _onchange_update_slug(self):
        if self.mailing_origin_id.name:
            self.mailing_slug = self.mailing_origin_id.name

    @api.onchange('mailing_slug')
    def _onchange_mailing_slug(self):
        if self.mailing_slug:
            self.mailing_slug = slugify(self.mailing_slug)


class Mail(models.Model):
    _inherit = 'mail.mail'

    @job(default_channel='root.mass_mailing')
    @related_action(action='related_action_emails')
    @api.multi
    def send_sendgrid_job(self, mass_mailings):
        regex = r'(?<=")((?:https|http)://(?:www\.|)compassion\.ch[^"]*)(?=")'
        for msg in self.filtered(lambda e: e.state == 'outgoing'):
            slug = msg.mailing_id.mass_mailing_campaign_id.mailing_slug
            if slug:
                # Append a param. c (as campaign) to all Compassion URLs
                msg.mail_message_id.body = \
                    re.sub(regex, r'\1?c=' + slug, msg.mail_message_id.body)
        # Make send method callable in a job
        self.send_sendgrid()
        mass_mailings.write({'state': 'done'})
        return True
