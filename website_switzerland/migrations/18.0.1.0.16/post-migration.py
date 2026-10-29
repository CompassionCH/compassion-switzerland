import json
import logging
import re

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

# The group visit and Muskathlon e-mails are signed by the sender of the
# communication (the event Responsible) instead of a fixed staff member.
SIGNER_SUBSTITUTIONS = [
    (
        re.compile(
            r't-set="user" t-value="(?:registration\.event_id|meeting)\.user_id"'
        ),
        't-set="user" t-value="object.user_id"',
    ),
    (
        re.compile(
            r"Colin Ward,\s*cward@compassion\.ch,\s*0\d\d\s+\d{3}\s+\d\d\s+\d\d"
        ),
        '<t t-out="object.user_id.preferred_name"/> '
        '<t t-out="object.user_id.lastname"/>, '
        '<t t-out="object.user_id.email"/>',
    ),
    (
        re.compile(r"\bColin(?=,?\s+(?:von\s+)?Compassion)"),
        '<t t-out="object.user_id.preferred_name"/>',
    ),
]


@openupgrade.migrate()
def migrate(env, version):
    _sign_by_responsible(env)


def _sign_by_responsible(env):
    """Also run on a new database (hooks.py): the texts it loads from older
    migrations still name the former signers."""
    configs = (
        env["partner.communication.config"]
        .with_context(active_test=False)
        .search([("model", "=", "event.registration")])
    )
    configs.write(
        {
            "send_from": "dynamic",
            "sender_field_id": env.ref(
                "event.field_event_registration__event_user_id"
            ).id,
        }
    )
    _logger.info("Event registration rules sent from the Responsible: %s", configs.ids)

    # Raw SQL: the bodies are translated, each language is kept as it is.
    templates = configs.email_template_id
    if not templates:
        return
    env.cr.execute(
        "SELECT id, body_html FROM mail_template WHERE id IN %s",
        (tuple(templates.ids),),
    )
    for template_id, bodies in env.cr.fetchall():
        new_bodies = {}
        for lang, body in (bodies or {}).items():
            for pattern, replacement in SIGNER_SUBSTITUTIONS:
                body = pattern.sub(replacement, body)
            new_bodies[lang] = body
        if new_bodies != bodies:
            env.cr.execute(
                "UPDATE mail_template SET body_html = %s WHERE id = %s",
                (json.dumps(new_bodies), template_id),
            )
            _logger.info("Template %s signed by the Responsible", template_id)
    templates.invalidate_recordset(["body_html"])
