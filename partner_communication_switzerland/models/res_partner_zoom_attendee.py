##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import datetime
from enum import Enum

from odoo import api, fields, models

COLOR_MAPPING = {
    "invited": 0,
    "confirmed": 10,
    "declined": 1,
    "attended": 11,
    "missing": 6,
}


class ZoomCommunication(Enum):
    REGISTRATION = (
        "partner_communication_switzerland"
        ".config_onboarding_zoom_registration_confirmation"
    )
    LINK = "partner_communication_switzerland.config_onboarding_zoom_link"
    REMINDER = "partner_communication_switzerland.config_onboarding_zoom_reminder"


class ZoomAttendee(models.Model):
    _name = "res.partner.zoom.attendee"
    _inherit = ["mail.thread", "mail.activity.mixin", "cms.form.partner"]
    _description = "Visio Conference Attendee"
    _rec_name = "partner_id"
    _order = "id desc"

    partner_id = fields.Many2one("res.partner", "Partner", required=True, index=True)
    zoom_session_id = fields.Many2one(
        "res.partner.zoom.session",
        "Zoom session",
        required=True,
        index=True,
        ondelete="cascade",
    )
    state = fields.Selection(
        [
            ("invited", "Invited"),
            ("confirmed", "Confirmed"),
            ("attended", "Attended"),
            ("missing", "Didn't show up"),
            ("declined", "Declined"),
        ],
        default="invited",
        group_expand="_expand_states",
        tracking=True,
    )
    optional_message = fields.Text()
    color = fields.Integer(compute="_compute_color")
    inform_me_for_next_zoom = fields.Boolean(
        "I am not available", help="Please inform me for the next Zoom session"
    )
    link_received = fields.Boolean(default=False)

    _sql_constraints = [
        (
            "unique_participant",
            "unique(partner_id,zoom_session_id)",
            "This partner is already invited to this zoom session!",
        )
    ]

    def _compute_color(self):
        for attendee in self:
            attendee.color = COLOR_MAPPING.get(attendee.state)

    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).state.selection]

    @api.model_create_multi
    def create(self, vals_list):
        res = self
        vals_list_to_create = vals_list.copy()

        for vals in vals_list:
            if vals.get("partner_id"):
                existing_attendee = self.search(
                    [
                        ("partner_id", "=", vals.get("partner_id")),
                        ("zoom_session_id", "=", vals.get("zoom_session_id")),
                    ]
                )
                if existing_attendee:
                    vals_list_to_create.remove(vals)
                    del vals["partner_id"]
                    del vals["zoom_session_id"]
                    existing_attendee.write(vals)
                    res += existing_attendee

            else:
                partner_vals = self._convert_vals_for_res_partner(vals)
                partner_id = (
                    self.env["res.partner.match"]
                    .match_values_to_partner(
                        partner_vals, match_update=False, match_create=False
                    )
                    .id
                )

                existing_attendee = self.search(
                    [
                        ("partner_id", "=", partner_id),
                        ("zoom_session_id", "=", vals.get("zoom_session_id")),
                    ]
                )
                if existing_attendee:
                    vals_list_to_create.remove(vals)
                    del vals["partner_firstname"]
                    del vals["partner_lastname"]
                    del vals["partner_email"]
                    del vals["zoom_session_id"]
                    existing_attendee.write(vals)
                    res += existing_attendee

        res += super().create(vals_list_to_create)

        for attendee in res:
            if attendee.inform_me_for_next_zoom:
                attendee.inform_about_next_session()
            if attendee.optional_message:
                attendee.notify_user()
        return res

    def inform_about_next_session(self):
        for attendee in self:
            attendee.state = "declined"
            next_zoom = attendee.zoom_session_id.get_next_session()
            if next_zoom:
                next_zoom.add_participant(attendee.partner_id)
            else:
                # Notify the staff
                lang = attendee.partner_id.lang[:2]
                user_id = self.env["res.config.settings"].get_param(
                    f"zoom_attendee_{lang}_id"
                )
                if user_id:
                    attendee.activity_schedule(
                        "mail.mail_activity_data_todo",
                        summary="Sponsor wants to attend the next Zoom session",
                        note="This person is not available for the upcoming zoom with "
                        "new sponsors, but wants to attend the next one. No "
                        "following session was found, please add him to "
                        "participants once it's created.",
                        user_id=user_id,
                    )

    def notify_user(self):
        self.ensure_one()
        lang = self.partner_id.lang[:2]
        user_id = self.env["res.config.settings"].get_param(f"zoom_attendee_{lang}_id")
        if user_id:
            self.activity_schedule(
                "mail.mail_activity_data_todo",
                summary="Participant registered for the zoom session with a message",
                note=self.optional_message,
                user_id=user_id,
            )

    def send_communication(self, config_name):
        self.ensure_one()
        config_id = self.env.ref(config_name.value).id
        partner_id = self.partner_id.id

        # avoid sending this twice communication
        if config_name == ZoomCommunication.LINK:
            if self.link_received:
                return self.env["partner.communication.job"]
            else:
                self.link_received = True

        if config_name in [ZoomCommunication.REMINDER, ZoomCommunication.LINK]:
            object_id = self.zoom_session_id.id
        elif config_name in [ZoomCommunication.REGISTRATION]:
            object_id = self.id
        else:
            object_id = None

        return self.env["partner.communication.job"].create(
            {
                "config_id": config_id,
                "partner_id": partner_id,
                "object_ids": object_id,
            }
        )

    def form_completion_callback(self):
        self.ensure_one()
        if (
            datetime.now()
            >= (self.zoom_session_id.date_send_link or self.zoom_session_id.date_start)
            and self.state != "declined"
        ):
            return self.send_communication(ZoomCommunication.LINK)
        return self.send_communication(ZoomCommunication.REGISTRATION)
