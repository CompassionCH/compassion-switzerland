import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    # The "before trip sharing information" mail sent 75 days before a group
    # visit was removed, but its rule stayed on the template and on the events
    # with no communication, which makes the event mail scheduler fail.
    rule = env.ref(
        "website_switzerland.group_visit_before_sharing_mail",
        raise_if_not_found=False,
    )
    if rule:
        rule.unlink()
    mails = env["event.mail"].search(
        [
            (
                "event_id.event_type_id",
                "=",
                env.ref("website_switzerland.event_type_group_visit").id,
            ),
            ("interval_type", "=", "before_event"),
            ("interval_nbr", "=", 75),
            ("interval_unit", "=", "days"),
            ("communication_id", "=", False),
            ("template_ref", "=", False),
            ("mail_done", "=", False),
        ]
    )
    _logger.info(
        "Empty 75 days before mails of the group visits removed: %s", mails.ids
    )
    mails.unlink()
