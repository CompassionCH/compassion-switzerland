##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models


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
        config_parameter="child_wp.sponsorship_notify_fr_id",
    )
    sponsorship_de_id = fields.Many2one(
        "res.partner",
        "New sponsorships (DE)",
        domain=[
            ("user_ids", "!=", False),
            ("user_ids.share", "=", False),
        ],
        config_parameter="child_wp.sponsorship_notify_de_id",
    )
    sponsorship_it_id = fields.Many2one(
        "res.partner",
        "New sponsorships (IT)",
        domain=[
            ("user_ids", "!=", False),
            ("user_ids.share", "=", False),
        ],
        config_parameter="child_wp.sponsorship_notify_fr_id",
    )
