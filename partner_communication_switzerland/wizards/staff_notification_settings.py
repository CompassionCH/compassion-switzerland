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
    zoom_attendee_fr_id = fields.Many2one(
        "res.users",
        "Zoom attendee (FR)",
        domain=[("share", "=", False)],
        readonly=False,
    )
    zoom_attendee_de_id = fields.Many2one(
        "res.users",
        "Zoom attendee (DE)",
        domain=[("share", "=", False)],
        readonly=False,
    )
    zoom_attendee_it_id = fields.Many2one(
        "res.users",
        "Zoom attendee (IT)",
        domain=[("share", "=", False)],
        readonly=False,
    )
    zoom_attendee_en_id = fields.Many2one(
        "res.users",
        "Zoom attendee (EN)",
        domain=[("share", "=", False)],
        readonly=False,
    )

    @api.multi
    def set_values(self):
        super().set_values()
        self.env["ir.config_parameter"].sudo().set_param(
            "partner_communication_switzerland.zoom_attendee_fr_id",
            str(
                self.zoom_attendee_fr_id.id
                if self.zoom_attendee_fr_id.id
                else 1
            ),
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "partner_communication_switzerland.zoom_attendee_de_id",
            str(
                self.zoom_attendee_de_id.id
                if self.zoom_attendee_de_id.id
                else 1
            ),
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "partner_communication_switzerland.zoom_attendee_it_id",
            str(
                self.zoom_attendee_it_id.id
                if self.zoom_attendee_it_id.id
                else 1
            ),
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "partner_communication_switzerland.zoom_attendee_en_id",
            str(
                self.zoom_attendee_en_id.id
                if self.zoom_attendee_en_id.id
                else 1
            ),
        )

    @api.model
    def get_values(self):
        res = super().get_values()
        param_obj = self.env["ir.config_parameter"].sudo()
        res.update(
            {
                "zoom_attendee_fr_id": int(
                    param_obj.get_param(
                        "partner_communication_switzerland.zoom_attendee_fr_id", None
                    )
                    or 0
                )
                or False,
                "zoom_attendee_de_id": int(
                    param_obj.get_param(
                        "partner_communication_switzerland.zoom_attendee_de_id", None
                    )
                    or 0
                )
                or False,
                "zoom_attendee_it_id": int(
                    param_obj.get_param(
                        "partner_communication_switzerland.zoom_attendee_it_id", None
                    )
                    or 0
                )
                or False,
                "zoom_attendee_en_id": int(
                    param_obj.get_param(
                        "partner_communication_switzerland.zoom_attendee_en_id", None
                    )
                    or 0
                )
                or False,
            }
        )
        return res
