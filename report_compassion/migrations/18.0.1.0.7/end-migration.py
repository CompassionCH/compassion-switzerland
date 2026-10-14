import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

# PDFs of these reports were rendered with broken accents (no charset) before
# 18.0.1.0.7. Communications keep their attachments until sent, so re-render
# the ones not sent yet, one job per attachment.
CERTIFICATE = "report_compassion.ending_sponsorship_certificate"
COVER = "report_compassion.blank_communication"


@openupgrade.migrate()
def migrate(env, version):
    attachments = env["partner.communication.attachment"].search(
        [
            ("report_name", "in", [CERTIFICATE, COVER]),
            ("communication_id.state", "in", ["pending", "failure"]),
        ]
    )
    attachments.with_delay_sh(
        "rerender_certificate_pdf",
        split=1,
        channel="root.partner_communication",
    )
    _logger.info(
        "T3500: queued %s jobs to re-render certificate/cover PDFs of unsent "
        "communications",
        len(attachments),
    )
