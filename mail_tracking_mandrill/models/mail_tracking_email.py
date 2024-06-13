# Copyright 2021 Compassion CH (http://www.compassion.ch)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class MailTrackingEmail(models.Model):
    _inherit = "mail.tracking.email"

    @property
    def _mandrill_event_type_mapping(self):
        """Map mandrill names to `mail.tracking` names"""
        return {
            "open": "open",
            "deferral": "deferral",
            "hard_bounce": "hard_bounce",
            "soft_bounce": "soft_bounce",
            "spam": "spam",
            "unsub": "unsub",
            "reject": "reject",
            "click": "click",
        }

    def _mandrill_event_type_verify(self, event):
        """
        Is requested mandrill event supported
        :param event: the event as a dictionary
        :return: [True/ False]
        """
        event = event or {}
        mandrill_event_type = event.get("event")
        if mandrill_event_type not in self._mandrill_event_type_mapping.keys():
            _logger.error(
                "Mandrill: event type {} not supported".format(mandrill_event_type)
            )
            return False

        return True

    def _mandrill_tracking_get(self, event):
        """
        Get tracking_email object referenced by event in request
        :param event: the event as a dictionary
        :return: tracking_email if found else False
        """
        tracking = False
        msg = event.get("msg", {})
        metadata = msg.get("metadata", {})
        tracking_email_id = metadata.get("tracking_email_id", False)
        if tracking_email_id and isinstance(tracking_email_id, int):
            tracking = self.browse(tracking_email_id)
        return tracking

    def _mandrill_metadata(self, event, metadata):
        """
        Prepare meta-data for event creation.
        :param event: the event as a dictionary
        :return: metadata in a dictionary format
        """
        msg = event.get("msg", False)
        if not msg:
            return {}
        ts = msg.get("ts", 0)
        time = datetime.datetime.fromtimestamp(ts)
        tags = msg.get("tags", [])

        ip = event.get("ip", False)
        url = event.get("url", False)
        # reject can be None
        reject = msg.get("reject", {}) or {}

        metadata.update(
            {
                "timestamp": ts,
                "time": time.strftime("%Y-%m-%d %H:%M:%S") if ts else False,
                "date": time.strftime("%Y-%m-%d") if ts else False,
                "recipient": msg.get("email"),
                "sender": msg.get("sender"),
                "name": msg.get("subject"),
                "tags": ", ".join(tags) if tags else False,
                "ip": ip,
                "url": url,
                "error_smtp_server": msg.get("diag"),
                "error_type": reject.get("reason") or "",
                "bounce_description": msg.get("bounce_description"),
            }
        )
        return metadata

    @api.model
    def event_process(self, request, post, metadata, event_type=None):
        super().event_process(request, post, metadata, event_type)

        res = []

        # iterate trough each event in mandrill_events key
        for event_raw in post.get("mandrill_events", []):
            # check if event is supported
            if not self._mandrill_event_type_verify(event_raw):
                _logger.error("Mandrill: skip to next event.")
                continue

            mandrill_event_type = event_raw.get("event")
            mapped_event_type = (
                self._mandrill_event_type_mapping.get(mandrill_event_type) or event_type
            )

            if not mapped_event_type:
                res.append("Error: Bad Event")

            # retrieve related mail
            tracking = self._mandrill_tracking_get(event_raw)

            if not tracking:
                res.append("Error: Tracking not found")

            # create event
            if tracking and mapped_event_type:
                res.append("OK")
                _metadata = self._mandrill_metadata(event_raw, metadata)
                tracking.event_create(mapped_event_type, _metadata)

        return ", ".join(res)
