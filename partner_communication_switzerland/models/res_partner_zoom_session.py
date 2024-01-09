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

from datetime import datetime, timedelta
from .res_partner_zoom_attendee import ZoomCommunication

from odoo import api, models, fields, _

logger = logging.getLogger(__name__)


class ZoomSession(models.Model):
    _name = "res.partner.zoom.session"
    _inherit = ["translatable.model", "website.published.mixin"]
    _description = "Sponsors Visio Conference"
    _rec_name = "date_start"
    _order = "date_start desc"

    lang = fields.Selection("_get_lang", required=True)
    date_start = fields.Datetime("Session time", required=True)
    date_stop = fields.Datetime()
    date_send_link = fields.Datetime("Reminder/link sent")
    link = fields.Char("Invitation link", required=True)
    participant_ids = fields.One2many(
        "res.partner.zoom.attendee", "zoom_session_id", "Participants"
    )
    state = fields.Selection([
        ("planned", "Planned"),
        ("done", "Done"),
        ("cancel", "Cancelled")
    ], required=True, default="planned")
    is_published = fields.Boolean(compute="_compute_website_published")
    number_participants = fields.Integer(compute="_compute_number_participants")

    @api.model
    def _get_lang(self):
        langs = self.env["res.lang"].search([])
        return [(l.code, l.name) for l in langs]

    @api.multi
    def _compute_website_url(self):
        for record in self:
            record.website_url = f'/zoom/{record.id}/register'

    @api.multi
    def _compute_website_published(self):
        for record in self:
            record.is_published = record.state == "planned"

    @api.multi
    def _compute_number_participants(self):
        for zoom in self:
            zoom.number_participants = len(zoom.participant_ids)

    @api.onchange("date_start")
    def onchange_date_start(self):
        if self.date_start:
            self.date_stop = self.date_start + timedelta(hours=1)

    @api.multi
    def post_attended(self):
        participants = self.mapped("participant_ids")
        participants.filtered(lambda p: p.state == "confirmed").write({
            "state": "attended"})
        participants.filtered(lambda p: p.state == "invited").write({
            "state": "declined"})
        self.write({"state": "done"})
        return True

    @api.model
    def get_next_session(self, date_start=None):
        """ Returns the next session (depending on context language) """
        if date_start is None:
            if self and len(self) == 1:
                date_start = fields.Datetime.to_string(self.date_start)
            else:
                date_start = fields.Datetime.now()
        elif not isinstance(date_start, str):
            date_start = fields.Datetime.to_string(date_start)
        return self.search([
            ("state", "=", "planned"),
            ("lang", "=", self.env.lang),
            ("date_start", ">", date_start)
        ], order="date_start asc", limit=1)

    @api.multi
    def send_reminder_or_link(self):
        communications = self.env["partner.communication.job"]
        for zoom in self.filtered(lambda z: z.state == "planned"):
            for participant in zoom.mapped("participant_ids").filtered(
                    lambda p: p.state in ("invited", "confirmed")):
                if participant.state in ["invited"]:
                    communications += participant.send_communication(
                        ZoomCommunication.REMINDER)
                elif participant.state in ["confirmed"]:
                    communications += participant.send_communication(
                        ZoomCommunication.LINK)
            zoom.date_send_link = fields.Datetime.now()
        return communications

    @api.multi
    def add_participant(self, partners):
        """
        Adds partners to the meeting
        :param partners: <res.partner> recordset
        :return: True
        """
        if self.state == "planned":
            self.participant_ids.create([{
                "partner_id": p.id,
                "zoom_session_id": self.id
            } for p in partners if p not in self.participant_ids.mapped("partner_id")])
        return True

    @api.multi
    def cancel(self):
        return self.write({"state": "cancel"})

    def edit_participants(self):
        return {
            "name": _("Participants"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "kanban,tree,form",
            "res_model": "res.partner.zoom.attendee",
            "context": self.env.context,
            "domain": [("zoom_session_id", "=", self.id)],
            "target": "current",
        }
