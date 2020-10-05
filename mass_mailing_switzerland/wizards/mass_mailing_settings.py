##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields


class MassMailingSettings(models.TransientModel):
    """ Settings configuration for any Notifications."""

    _inherit = "res.config.settings"

    # Select which fund will be used for mass mailing donation links
    mass_mailing_donation_fund_id = fields.Many2one(
        "product.template",
        "Fund donation for mass mailing links",
        readonly=False,
    )
    mass_mailing_country_filter_id = fields.Many2one(
        "compassion.field.office",
        "Filter sponsor child selection for mass mailing",
        readonly=False
    )

    @api.multi
    def set_values(self):
        super().set_values()
        self.env["ir.config_parameter"].sudo().set_param(
            "mass_mailing_switzerland.donation_fund_id",
            str(
                self.mass_mailing_donation_fund_id.id or 0
            ),
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "mass_mailing_switzerland.country_filter_id",
            str(
                self.mass_mailing_country_filter_id.id or 0
            ),
        )
        # Recompute mailchimp merge fields
        self.env["mail.mass_mailing.contact"].with_delay().update_all_merge_fields_job()

    @api.model
    def get_values(self):
        res = super().get_values()
        param_obj = self.env["ir.config_parameter"].sudo()
        res.update({
            "mass_mailing_donation_fund_id": int(param_obj.get_param(
                "mass_mailing_switzerland.donation_fund_id", None
            ) or 0) or False,
            "mass_mailing_country_filter_id": int(param_obj.get_param(
                "mass_mailing_switzerland.country_filter_id", None
            ) or 0) or False,
        })
        return res
