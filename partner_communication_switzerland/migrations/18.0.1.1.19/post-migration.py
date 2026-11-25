from openupgradelib import openupgrade

# The v14 website sponsorship confirmation and reminder e-mails link to a
# MyCompassion 1.0 page that no longer exists. Their automation is removed
# from the module data; the configs and templates are noupdate, so they are
# archived here, which keeps the history of the jobs already sent.
RETIRED = (
    "partner_communication_switzerland.sms_registration_confirmation_1",
    "partner_communication_switzerland.sms_registration_reminder",
    "partner_communication_switzerland.sms_confirmation_email_1",
    "partner_communication_switzerland.sms_reminder_email",
)


@openupgrade.migrate()
def migrate(env, version):
    for xmlid in RETIRED:
        record = env.ref(xmlid, raise_if_not_found=False)
        if record:
            record.active = False
