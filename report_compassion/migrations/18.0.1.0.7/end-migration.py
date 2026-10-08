import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

# PDFs of these reports were rendered with broken accents (no charset) before
# 18.0.1.0.7. Communications keep their attachments until sent, so re-render
# the ones not sent yet. End-migration: the generating methods live in
# partner_communication_switzerland, which loads after this module.
CERTIFICATE = "report_compassion.ending_sponsorship_certificate"
COVER = "report_compassion.blank_communication"


def _render(job, report_name):
    job = job.with_context(lang=job.partner_id.lang, must_skip_send_to_printer=True)
    if report_name == COVER:
        binaries = job.get_blank_communication_attachment()
    elif job.config_id.attachments_function == (
        "get_end_sponsorship_certificate_new_version"
    ):
        binaries = job.get_end_sponsorship_certificate_new_version()
    else:
        binaries = job.get_end_sponsorship_certificate()
    return next(iter(binaries.values()))[1]


@openupgrade.migrate()
def migrate(env, version):
    attachments = env["partner.communication.attachment"].search(
        [
            ("report_name", "in", [CERTIFICATE, COVER]),
            ("communication_id.state", "in", ["pending", "failure"]),
        ]
    )
    failed = 0
    for attachment in attachments:
        try:
            with env.cr.savepoint():
                attachment.attachment_id.datas = _render(
                    attachment.communication_id, attachment.report_name
                )
        except Exception:
            failed += 1
            _logger.warning(
                "T3500: could not re-render %s for communication %s",
                attachment.report_name,
                attachment.communication_id.id,
                exc_info=True,
            )
    _logger.info(
        "T3500: re-rendered %s certificate/cover PDFs of unsent communications "
        "(%s failed)",
        len(attachments) - failed,
        failed,
    )
