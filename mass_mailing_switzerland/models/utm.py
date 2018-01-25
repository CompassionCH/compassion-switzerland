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
