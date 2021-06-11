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

from dateutil.relativedelta import relativedelta

from odoo import api, models, fields

logger = logging.getLogger(__name__)


class ZoomSession(models.Model):
    _name = "res.partner.zoom.session"
    _inherit = ["translatable.model", "website.published.mixin"]
    _description = "Zoom Session with partners"
    _rec_name = "date_start"
    _order = "date_start desc"

    lang = fields.Selection("_get_lang", required=True)
    date_start = fields.Datetime("Zoom session time", required=True)
    date_stop = fields.Datetime()
    link = fields.Char("Invitation link")
    meeting_id = fields.Char("Meeting ID")
    passcode = fields.Char("Passcode")
    participant_ids = fields.One2many(
        "res.partner.zoom.attendee", "zoom_session_id", "Participants"
    )
    state = fields.Selection([
        ("planned", "Planned"),
        ("done", "Done"),
        ("cancel", "Cancelled")
    ], required=True, default="planned")
    is_published = fields.Boolean(compute="_compute_website_published")

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

    @api.onchange("date_start")
    def onchange_date_start(self):
        if self.date_start:
            self.date_stop = self.date_start + relativedelta(hours=1)

    @api.multi
    def post_attended(self):
        participants = self.mapped("participant_ids")
        confirmed = participants.filtered(lambda p: p.state == "confirmed")
        confirmed.write({"state": "attended"})
        (participants - confirmed).write({"state": "declined"})
        self.write({"state": "done"})
        return True

    @api.model
    def get_next_session(self, date_start=None):
        """ Returns the next session (depending on context language) """
        if date_start is None:
            date_start = fields.Date.today()
        if self and len(self) == 1:
            date_start = fields.Date.to_string(self.date_start)
        return self.search([
            ("state", "=", "planned"),
            ("lang", "=", self.env.lang),
            ("date_start", ">=", date_start)
        ], order="date_start asc", limit=1)

    @api.multi
    def send_reminder(self):
        pending_config = self.env.ref(
            "partner_communication_switzerland.config_onboarding_zoom_reminder")
        attending_config = self.env.ref(
            "partner_communication_switzerland.config_onboarding_zoom_link")
        communications = self.env["partner.communication.job"]
        for zoom in self.filtered(lambda z: z.state == "planned"):
            for participant in zoom.mapped("participant_ids").filtered(
                    lambda p: p.state in ("invited", "confirmed")):
                communications += self.env["partner.communication.job"].create({
                    "config_id": (
                        attending_config if participant.state == "confirmed"
                        else pending_config).id,
                    "partner_id": participant.partner_id.id,
                    "object_ids": zoom.id
                })
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
            } for p in partners])
        return True

    @api.multi
    def cancel(self):
        return self.write({"state": "cancel"})
