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
    _description = "Zoom Session with partners"
    _rec_name = "date_start"
    _order = "date_start desc"

    lang = fields.Selection("_get_lang", required=True)
    date_start = fields.Datetime("Zoom session time", required=True)
    date_stop = fields.Datetime()
    link = fields.Char("Zoom invitation link")
    passcode = fields.Char("Zoom password")
    invited_participant_ids = fields.Many2many(
        "res.partner", "zoom_invited_partner_ids", "zoom_session_id", "partner_id",
        "Invited people"
    )
    attended_participant_ids = fields.Many2many(
        "res.partner", "zoom_attended_partner_ids", "zoom_session_id", "partner_id",
        "Attended people"
    )
    state = fields.Selection([
        ("planned", "Planned"),
        ("done", "Done")
    ], required=True, default="planned")

    @api.model
    def _get_lang(self):
        langs = self.env["res.lang"].search([])
        return [(l.code, l.name) for l in langs]

    @api.onchange("date_start")
    def onchange_date_start(self):
        if self.date_start:
            self.date_stop = self.date_start + relativedelta(hours=1)

    @api.multi
    def post_attended(self):
        for zoom in self:
            zoom.write({
                "state": "done",
                "attended_participant_ids": [(6, 0, zoom.invited_participant_ids.ids)]
            })
        return True

    @api.model
    def get_next_session(self):
        """ Returns the next session (depending on context language) """
        return self.search([
            ("state", "=", "planned"),
            ("lang", "=", self.env.lang)
        ], order="date_start asc", limit=1)

    @api.multi
    def send_reminder(self):
        config = self.env.ref("partner_communication_switzerland"
                              ".config_onboarding_zoom_reminder")
        for zoom in self:
            for participant in self.invited_participant_ids:
                self.env["partner.communication.job"].create({
                    "config_id": config.id,
                    "partner_id": participant.id,
                    "object_ids": zoom.id
                })

    @api.multi
    def add_participant(self, partners):
        """
        Adds partners to the meeting
        :param partners: <res.partner> recordset
        :return: True
        """
        self.ensure_one()
        if self.state == "planned":
            self.invited_participant_ids += partners
        return True
