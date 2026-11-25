from openupgradelib import openupgrade

# The v14 website sponsorship confirmation and reminder e-mails link to a
# MyCompassion 1.0 page that no longer exists. Their automation is removed
# from the module data; the configs and templates are noupdate, so they are
# archived here, which keeps the history of the jobs already sent.
CONFIGS = (
    "partner_communication_switzerland.sms_registration_confirmation_1",
    "partner_communication_switzerland.sms_registration_reminder",
)
TEMPLATES = (
    "partner_communication_switzerland.sms_confirmation_email_1",
    "partner_communication_switzerland.sms_reminder_email",
)


def cancel_unsent(env, configs):
    """Cancel the communications of these configs not sent yet, and their
    queued e-mail task: archiving a config does not stop them."""
    jobs = env["partner.communication.job"].search(
        [
            ("config_id", "in", configs.ids),
            ("state", "in", ("pending", "processing")),
        ]
    )
    if not jobs:
        return
    keys = [f"partner.communication.job._send_mail.{job.id}" for job in jobs]
    env["queue.job"].search(
        [
            ("identity_key", "in", keys),
            ("state", "in", ("wait_dependencies", "pending", "enqueued")),
        ]
    ).button_cancelled()
    jobs.cancel()


@openupgrade.migrate()
def migrate(env, version):
    configs = env["partner.communication.config"]
    for xmlid in CONFIGS:
        configs |= env.ref(xmlid, raise_if_not_found=False) or configs
    cancel_unsent(env, configs)
    configs.write({"active": False})
    for xmlid in TEMPLATES:
        template = env.ref(xmlid, raise_if_not_found=False)
        if template:
            template.active = False
