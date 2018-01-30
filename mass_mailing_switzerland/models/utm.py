# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields


class UtmMixin(models.AbstractModel):
    _inherit = 'utm.mixin'

    def get_utms(self, utm_source=False, utm_medium=False, utm_campaign=False):
        """
        Finds the utm records given their name
        :param utm_source:
        :param utm_medium:
        :param utm_campaign:
        :return: dictionary with utm ids
        """
        utm_source_id = False
        if utm_source:
            utm_source_id = self.env['utm.source'].search([
                ('name', '=', utm_source)
            ], limit=1).id
        utm_medium_id = False
        if utm_medium:
            utm_medium_id = self.env['utm.medium'].search([
                ('name', '=', utm_medium)
            ], limit=1).id or utm_medium_id
        utm_campaign_id = False
        if utm_campaign:
            utm_campaign_id = self.env['utm.campaign'].search([
                ('name', '=', utm_campaign)
            ], limit=1).id
        return {
            'source': utm_source_id,
            'medium': utm_medium_id,
            'campaign': utm_campaign_id
        }


class UtmSource(models.Model):
    _inherit = 'utm.source'

    contract_ids = fields.One2many(
        'recurring.contract', 'source_id', 'Sponsorships',
        readonly=True
    )
    correspondence_ids = fields.One2many(
        'correspondence', 'source_id', 'Sponsor letters',
        readonly=True
    )
    invoice_ids = fields.One2many(
        'account.invoice', 'source_id', 'Donations', readonly=True
    )


class UtmCampaign(models.Model):
    _inherit = 'utm.campaign'

    contract_ids = fields.One2many(
        'recurring.contract', 'campaign_id', 'Sponsorships',
        readonly=True
    )
    correspondence_ids = fields.One2many(
        'correspondence', 'campaign_id', 'Sponsor letters',
        readonly=True
    )
    invoice_ids = fields.One2many(
        'account.invoice', 'campaign_id', 'Donations', readonly=True
    )


class UtmMedium(models.Model):
    _inherit = 'utm.medium'

    contract_ids = fields.One2many(
        'recurring.contract', 'medium_id', 'Sponsorships',
        readonly=True
    )
    correspondence_ids = fields.One2many(
        'correspondence', 'medium_id', 'Sponsor letters',
        readonly=True
    )
    invoice_ids = fields.One2many(
        'account.invoice', 'medium_id', 'Donations', readonly=True
    )
