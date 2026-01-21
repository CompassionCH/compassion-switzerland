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

    # Notify for advocate birthdays
    advocate_birthday_fr_id = fields.Many2one(
        "res.partner",
        "Advocate birthday (FR)",
        domain=[
            ("user_ids", "!=", False),
            ("user_ids.share", "=", False),
        ],
        config_parameter="partner_compassion.advocate_birthday_fr_id",
    )
    advocate_birthday_de_id = fields.Many2one(
        "res.partner",
        "Advocate birthday (DE)",
        domain=[
            ("user_ids", "!=", False),
            ("user_ids.share", "=", False),
        ],
        config_parameter="partner_compassion.advocate_birthday_de_id",
    )
    advocate_birthday_it_id = fields.Many2one(
        "res.partner",
        "Advocate birthday (IT)",
        domain=[
            ("user_ids", "!=", False),
            ("user_ids.share", "=", False),
        ],
        config_parameter="partner_compassion.advocate_birthday_it_id",
    )
    advocate_birthday_en_id = fields.Many2one(
        "res.partner",
        "Advocate birthday (EN)",
        domain=[
            ("user_ids", "!=", False),
            ("user_ids.share", "=", False),
        ],
        config_parameter="partner_compassion.advocate_birthday_en_id",
    )
    potential_advocate_fr = fields.Many2one(
        "res.users",
        "Potential advocate FR",
        domain=[("share", "=", False)],
        config_parameter="partner_communication_switzerland.potential_advocate_fr",
    )
    potential_advocate_de = fields.Many2one(
        "res.users",
        "Potential advocate DE",
        domain=[("share", "=", False)],
        config_parameter="partner_communication_switzerland.potential_advocate_de",
    )
    potential_advocate_it = fields.Many2one(
        "res.users",
        "Potential advocate IT",
        domain=[("share", "=", False)],
        config_parameter="partner_communication_switzerland.potential_advocate_it",
    )
