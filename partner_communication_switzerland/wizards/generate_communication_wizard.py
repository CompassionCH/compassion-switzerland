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

from math import ceil

from odoo import models, api, fields
from odoo.tools.safe_eval import safe_eval

SMS_CHAR_LIMIT = 160
SMS_COST = 0.08

_logger = logging.getLogger(__name__)

try:
    from bs4 import BeautifulSoup
except ImportError:
    _logger.warning("Please install bs4 for using the module")


class GenerateCommunicationWizard(models.TransientModel):
    _inherit = "partner.communication.generate.wizard"

    sponsorship_ids = fields.Many2many(
        "recurring.contract", string="Sponsorships",
        compute="_compute_sponsorships"
    )
    res_model = fields.Selection(
        [("res.partner", "Partners"), ("recurring.contract", "Sponsorships")],
        "Source",
        default="res.partner",
        required=True,
    )
    partner_source = fields.Selection(
        [
            ("partner_id", "Payer"),
            ("send_gifts_to", "Gift payer"),
            ("correspondent_id", "Correspondent"),
        ],
        "Send to",
        default="correspondent_id",
        required=True,
    )
    # Remove domain filter and handle it in the view
    model_id = fields.Many2one(domain=[], readonly=False, required=True)
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

    @api.multi
    def _compute_progress(self):
        s_wizards = self.filtered(lambda w: w.res_model == "recurring.contract")
        for wizard in s_wizards:
            if wizard.partner_source == "send_gifts_to":
                partners = self.env["res.partner"]
                for sponsorship in wizard.sponsorship_ids:
                    partners += sponsorship.mapped(sponsorship.send_gifts_to)
            else:
                partners = wizard.sponsorship_ids.mapped(wizard.partner_source)

            wizard.progress = float(len(wizard.communication_ids) * 100) // (
                len(partners) or 1
            )
        super(GenerateCommunicationWizard, self - s_wizards)._compute_progress()

    @api.multi
    @api.depends("sms_number_estimation")
    def _compute_sms_cost_estimation(self):
        for wizard in self:
            wizard.sms_cost_estimation = wizard.sms_number_estimation * SMS_COST

    @api.multi
    def _compute_currency(self):
        chf = self.env.ref("base.CHF")
        for wizard in self:
            wizard.currency_id = chf.id

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.depends("selection_domain", "res_model")
    def _compute_partners(self):
        if self.res_model == "recurring.contract":
            if self.partner_source == "send_gifts_to":
                # We assume the payer and the correspondent speak same lang
                partner_source = "correspondent_id"
            else:
                partner_source = self.partner_source
            if self.selection_domain:
                self.sponsorship_ids = self.env["recurring.contract"].search(
                    safe_eval(self.selection_domain)
                )
                if self.partner_source == "send_gifts_to":
                    partners = self.env["res.partner"]
                    for sponsorship in self.sponsorship_ids:
                        partners += sponsorship.mapped(sponsorship.send_gifts_to)
                else:
                    partners = self.sponsorship_ids.mapped(partner_source)
                self.partner_ids = partners
        else:
            super()._compute_partners()

    @api.depends("selection_domain", "res_model")
    def _compute_sponsorships(self):
        if self.res_model == "recurring.contract" and self.selection_domain:
            self.sponsorship_ids = self.env["recurring.contract"].search(
                safe_eval(self.selection_domain))

    def generate_communications(self, async_mode=True):
        """ Create the communication records """
        wizard = self.with_context(
            default_utm_campaign_id=self.campaign_id.id,
            default_sms_provider_id=self.sms_provider_id.id,
        )
        if self.res_model == "recurring.contract":
            for sponsorship in self.sponsorship_ids:
                if self.partner_source == "send_gifts_to":
                    partner = sponsorship.mapped(sponsorship.send_gifts_to)
                else:
                    partner = sponsorship.mapped(self.partner_source)
                vals = {
                    "partner_id": partner.id,
                    "object_ids": sponsorship.id,
                    "config_id": self.model_id.id,
                }
                if self.send_mode:
                    vals.update({
                        "send_mode": self.send_mode,
                        "auto_send": False,
                    })
                if async_mode:
                    wizard.with_delay().create_communication(vals)
                else:
                    wizard.create_communication(vals)
            return True
        else:
            return super(GenerateCommunicationWizard, wizard).generate_communications(
                async_mode
            )
