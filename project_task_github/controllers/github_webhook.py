# Copyright 2026 Compassion CH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import hashlib
import hmac
import json
import logging

from odoo import http
from odoo.http import request
from odoo.tools import config

_logger = logging.getLogger(__name__)

DELIVERY_HEADER = "X-GitHub-Delivery"
EVENT_HEADER = "X-GitHub-Event"
SIGNATURE_HEADER = "X-Hub-Signature-256"


class GithubWebhookController(http.Controller):
    @http.route(
        "/github/webhook",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
        save_session=False,
    )
    def github_webhook(self):
        """Receive the pull request events of the GitHub organisation."""
        headers = request.httprequest.headers
        delivery = headers.get(DELIVERY_HEADER, "?")

        secret = config.get("github_webhook_secret")
        if not secret:
            _logger.error(
                "Received GitHub delivery %s but 'github_webhook_secret' is "
                "missing from the [options] section of the Odoo configuration "
                "file. The request cannot be authenticated and is discarded.",
                delivery,
            )
            return request.make_response("NOT_CONFIGURED", status=503)

        body = request.httprequest.get_data()
        signature = (
            "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        )
        if not hmac.compare_digest(signature, headers.get(SIGNATURE_HEADER, "")):
            _logger.warning("Invalid signature for GitHub delivery %s.", delivery)
            return request.make_response("BAD_SIGNATURE", status=401)

        event = headers.get(EVENT_HEADER)
        if event == "ping":
            return request.make_response("PONG")
        if event != "pull_request":
            return request.make_response("IGNORED")

        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            _logger.error(
                "The body of GitHub delivery %s is not JSON. The content type "
                "of the webhook must be set to application/json.",
                delivery,
            )
            return request.make_response("BAD_PAYLOAD", status=400)

        if payload.get("action") not in ("opened", "edited"):
            return request.make_response("IGNORED")

        pull_request = payload["pull_request"]
        task = request.env["project.task"]._find_by_github_reference(
            pull_request["title"], pull_request["head"]["ref"]
        )
        if not task:
            _logger.info(
                "GitHub delivery %s: no task matches pull request %s (%s).",
                delivery,
                pull_request["html_url"],
                pull_request["title"],
            )
            return request.make_response("NO_TASK")

        task._set_github_pr_uri(pull_request["html_url"])
        return request.make_response("OK")
