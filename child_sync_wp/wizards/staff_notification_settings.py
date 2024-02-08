##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, fields, models


class StaffNotificationSettings(models.TransientModel):
    """Settings configuration for any Notifications."""

    _inherit = "res.config.settings"

    # Users to notify when new Sponsorship is made
    sponsorship_fr_id = fields.Many2one(
        "res.partner",
        "New sponsorships (FR)",
        domain=[
            ("user_ids", "!=", False),
            ("user_ids.share", "=", False),
        ],
        readonly=False,
    )
    sponsorship_de_id = fields.Many2one(
        "res.partner",
        "New sponsorships (DE)",
        domain=[
            ("user_ids", "!=", False),
            ("user_ids.share", "=", False),
        ],
        readonly=False,
    )
    sponsorship_it_id = fields.Many2one(
        "res.partner",
        "New sponsorships (IT)",
        domain=[
            ("user_ids", "!=", False),
            ("user_ids.share", "=", False),
        ],
        readonly=False,
    )

    def get_sponsorship_fr_id(self):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("child_wp.sponsorship_notify_fr_id", None)
        )

    def get_sponsorship_de_id(self):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("child_wp.sponsorship_notify_de_id", None)
        )

    def get_sponsorship_it_id(self):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("child_wp.sponsorship_notify_it_id", None)
        )

    @api.model
    def get_values(self):
        res = super().get_values()
        res.update(
            {
                "sponsorship_fr_id": int(self.get_sponsorship_fr_id() or 0) or False,
                "sponsorship_de_id": int(self.get_sponsorship_de_id() or 0) or False,
                "sponsorship_it_id": int(self.get_sponsorship_it_id() or 0) or False,
            }
        )
        return res

    def set_values(self):
        super().set_values()
        self.env["ir.config_parameter"].sudo().set_param(
            "child_wp.sponsorship_notify_fr_id", str(self.sponsorship_fr_id.id or 0)
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "child_wp.sponsorship_notify_de_id", str(self.sponsorship_de_id.id or 0)
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "child_wp.sponsorship_notify_it_id", str(self.sponsorship_it_id.id or 0)
        )
