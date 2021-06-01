##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields


class StaffNotificationSettings(models.TransientModel):
    """ Settings configuration for any Notifications."""

    _inherit = "res.config.settings"

    # Notify for advocate birthdays
    advocate_birthday_fr_id = fields.Many2one(
        "res.partner",
        "Advocate birthday (FR)",
        domain=[("user_ids", "!=", False), ("user_ids.share", "=", False), ],
        readonly=False,
    )
    advocate_birthday_de_id = fields.Many2one(
        "res.partner",
        "Advocate birthday (DE)",
        domain=[("user_ids", "!=", False), ("user_ids.share", "=", False), ],
        readonly=False,
    )
    advocate_birthday_it_id = fields.Many2one(
        "res.partner",
        "Advocate birthday (IT)",
        domain=[("user_ids", "!=", False), ("user_ids.share", "=", False), ],
        readonly=False,
    )
    advocate_birthday_en_id = fields.Many2one(
        "res.partner",
        "Advocate birthday (EN)",
        domain=[("user_ids", "!=", False), ("user_ids.share", "=", False), ],
        readonly=False,
    )
    share_on_nas = fields.Text()
    store_path = fields.Text()
    potential_advocate_fr = fields.Many2one(
        "res.users", "Potential advocate FR", domain=[("share", "=", False)]
    )
    potential_advocate_de = fields.Many2one(
        "res.users", "Potential advocate DE", domain=[("share", "=", False)]
    )
    potential_advocate_it = fields.Many2one(
        "res.users", "Potential advocate IT", domain=[("share", "=", False)]
    )

    @api.multi
    def set_values(self):
        super().set_values()
        self.env["ir.config_parameter"].sudo().set_param(
            "partner_compassion.advocate_birthday_fr_id",
            str(
                self.advocate_birthday_fr_id.id
                if self.advocate_birthday_fr_id.id
                else 1
            ),
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "partner_compassion.advocate_birthday_de_id",
            str(
                self.advocate_birthday_de_id.id
                if self.advocate_birthday_de_id.id
                else 1
            ),
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "partner_compassion.advocate_birthday_it_id",
            str(
                self.advocate_birthday_it_id.id
                if self.advocate_birthday_it_id.id
                else 1
            ),
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "partner_compassion.advocate_birthday_en_id",
            str(
                self.advocate_birthday_en_id.id
                if self.advocate_birthday_en_id.id
                else 1
            ),
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "partner_compassion.share_on_nas", self.share_on_nas
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "partner_compassion.store_path", self.store_path
        )
        self.env["ir.config_parameter"].set_param(
            "partner_communication_switzerland.potential_advocate_fr",
            str(self.potential_advocate_fr.id or 0))
        self.env["ir.config_parameter"].set_param(
            "partner_communication_switzerland.potential_advocate_de",
            str(self.potential_advocate_de.id or 0))
        self.env["ir.config_parameter"].set_param(
            "partner_communication_switzerland.potential_advocate_it",
            str(self.potential_advocate_it.id or 0))

    @api.model
    def get_values(self):
        res = super().get_values()
        param_obj = self.env["ir.config_parameter"].sudo()
        res.update(
            {
                "advocate_birthday_fr_id": int(
                    param_obj.get_param(
                        "partner_compassion.advocate_birthday_fr_id", None
                    )
                    or 0
                )
                or False,
                "advocate_birthday_de_id": int(
                    param_obj.get_param(
                        "partner_compassion.advocate_birthday_de_id", None
                    )
                    or 0
                )
                or False,
                "advocate_birthday_it_id": int(
                    param_obj.get_param(
                        "partner_compassion.advocate_birthday_it_id", None
                    )
                    or 0
                )
                or False,
                "advocate_birthday_en_id": int(
                    param_obj.get_param(
                        "partner_compassion.advocate_birthday_en_id", None
                    )
                    or 0
                )
                or False,
                "share_on_nas": str(
                    param_obj.get_param("partner_compassion.share_on_nas", "")
                ),
                "store_path": str(
                    param_obj.get_param("partner_compassion.store_path", "")
                ),
            }
        )
        user_fr = self.env["ir.config_parameter"].get_param(
            "partner_communication_switzerland.potential_advocate_fr", 0)
        res["potential_advocate_fr"] = int(user_fr)
        user_de = self.env["ir.config_parameter"].get_param(
            "partner_communication_switzerland.potential_advocate_de", 0)
        res["potential_advocate_de"] = int(user_de)
        user_it = self.env["ir.config_parameter"].get_param(
            "partner_communication_switzerland.potential_advocate_it", 0)
        res["potential_advocate_it"] = int(user_it)
        return res
