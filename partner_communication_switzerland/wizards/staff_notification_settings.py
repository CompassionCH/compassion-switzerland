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
    new_donors_user = fields.Many2one(
        "res.users", "User to notify on new donors onboarding opt out", readonly=False
    )
    invalid_mail_notify_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="invalid_mail_staff_notify_rel",
        column1="staff_id",
        column2="partner_id",
        string="Invalid email",
        domain=[
            ("user_ids", "!=", False),
            ("user_ids.share", "=", False),
        ],
        readonly=False,
    )

    def set_values(self):
        res = super().set_values()
        self.env["ir.config_parameter"].sudo().set_param(
            "partner_communication_switzerland.zoom_attendee_fr_id",
            str(self.zoom_attendee_fr_id.id if self.zoom_attendee_fr_id.id else 1),
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "partner_communication_switzerland.zoom_attendee_de_id",
            str(self.zoom_attendee_de_id.id if self.zoom_attendee_de_id.id else 1),
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "partner_communication_switzerland.zoom_attendee_it_id",
            str(self.zoom_attendee_it_id.id if self.zoom_attendee_it_id.id else 1),
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "partner_communication_switzerland.zoom_attendee_en_id",
            str(self.zoom_attendee_en_id.id if self.zoom_attendee_en_id.id else 1),
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "partner_communication_switzerland.new_donors_user",
            str(self.new_donors_user.id or 0),
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "partner_communication_switzerland.invalid_mail_notify_ids",
            ",".join(list(map(str, self.invalid_mail_notify_ids.ids))),
        )
        return res

    @api.model
    def get_values(self):
        res = super().get_values()
        param_obj = self.env["ir.config_parameter"].sudo()
        new_donors_user_id = int(
            param_obj.get_param(
                "partner_communication_switzerland.new_donors_user", "0"
            )
        )
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
                "new_donors_user": new_donors_user_id,
            }
        )
        res["invalid_mail_notify_ids"] = False
        partners = param_obj.get_param(
            "partner_communication_switzerland.invalid_mail_notify_ids", False
        )
        if partners:
            res["invalid_mail_notify_ids"] = list(map(int, partners.split(",")))
        return res


class PhoneReformat(models.TransientModel):
    _inherit = "reformat.all.phonenumbers"

    # Avoids relational table clash
    invalid_mail_notify_ids = fields.Many2many(
        "res.partner",
        compute="_compute_invalid_mail_notify_ids",
    )

    def _compute_invalid_mail_notify_ids(self):
        for record in self:
            record.invalid_mail_notify_ids = False
