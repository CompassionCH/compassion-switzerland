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

    mass_mailing_country_filter_id = fields.Many2one(
        "compassion.field.office",
        "Filter sponsor child selection for mass mailing",
        readonly=False
    )

    @api.multi
    def set_values(self):
        super().set_values()
        country_filter_id = self.mass_mailing_country_filter_id.id or 0
        if country_filter_id != self.get_param("mass_mailing_country_filter_id"):
            # Recompute mailchimp merge fields
            self.env["mail.mass_mailing.contact"].search([
                ("list_ids.mailchimp_list_id", "!=", False)
            ]).process_mailchimp_update()
            self.env["ir.config_parameter"].sudo().set_param(
                "mass_mailing_switzerland.country_filter_id",
                str(country_filter_id),
            )

    @api.model
    def get_values(self):
        res = super().get_values()
        param_obj = self.env["ir.config_parameter"].sudo()
        res.update({
            "mass_mailing_country_filter_id": int(param_obj.get_param(
                "mass_mailing_switzerland.country_filter_id", None
            ) or 0) or False,
        })
        return res
