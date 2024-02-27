##############################################################################
#
#    Copyright (C) 2021 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from datetime import datetime, timedelta

from werkzeug.exceptions import Unauthorized

from odoo import http
from odoo.http import Controller, request

_logger = logging.getLogger(__name__)


class ZoomRegistration(Controller):
    @http.route(
        [
            "/zoom/<model('res.partner.zoom.session'):session>/register",
            "/zoom/register",
        ],
        type="http",
        auth="public",
        methods=["GET", "POST"],
        website=True,
        sitemap=False,
    )
    def zoom_registration(self, session=None, **kwargs):
        if session is None:
            # Allow to register in the current zoom session for 15 minutes after start
            start = datetime.now() - timedelta(minutes=15)
            session = request.env["res.partner.zoom.session"].get_next_session(start)
        if not session.website_published:
            raise Unauthorized()
        participant = request.env["res.partner.zoom.attendee"]
        if request.env.user and request.env.user != request.env.ref("base.public_user"):
            partner = request.env.user.partner_id
            kwargs["partner_id"] = partner.id
            participant = session.participant_ids.filtered(
                lambda p: p.partner_id == partner
            )
        kwargs["zoom_session_id"] = session.id
        return request.render(
            "partner_communication_switzerland.zoom_registration_template",
            {"session": session, "main_object": participant},
        )
