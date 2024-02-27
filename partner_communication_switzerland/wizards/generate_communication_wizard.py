##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import api, fields, models

SMS_CHAR_LIMIT = 160
SMS_COST = 0.08

_logger = logging.getLogger(__name__)


class GenerateCommunicationWizard(models.TransientModel):
    _inherit = "partner.communication.generate.wizard"

    sms_length_estimation = fields.Integer(readonly=True)
    sms_number_estimation = fields.Integer(readonly=True)
    sms_cost_estimation = fields.Float(compute="_compute_sms_cost_estimation")
    currency_id = fields.Many2one(
        "res.currency", compute="_compute_currency", readonly=False
    )
    campaign_id = fields.Many2one("utm.campaign", "Campaign", readonly=False)
    sms_provider_id = fields.Many2one(
        "sms.provider",
        "SMS Provider",
        default=lambda self: self.env.ref("sms_939.large_account_id", False),
        readonly=False,
    )

    @api.depends("sms_number_estimation")
    def _compute_sms_cost_estimation(self):
        for wizard in self:
            wizard.sms_cost_estimation = wizard.sms_number_estimation * SMS_COST

    def _compute_currency(self):
        chf = self.env.ref("base.CHF")
        for wizard in self:
            wizard.currency_id = chf.id

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################

    def generate_communications(self, async_mode=True):
        """Create the communication records"""
        return super(
            GenerateCommunicationWizard,
            self.with_context(
                default_utm_campaign_id=self.campaign_id.id,
                default_sms_provider_id=self.sms_provider_id.id,
            ),
        ).generate_communications(async_mode)
