import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

NAMES = {
    "task_flight_details": {
        "en_US": "Give outbound flight",
        "fr_CH": "Indiquer le vol aller",
        "de_DE": "Hinflug angeben",
        "it_IT": "Indica il volo di andata",
    },
    "task_return_flight": {
        "en_US": "Give return flight",
        "fr_CH": "Indiquer le vol retour",
        "de_DE": "Rückflug angeben",
        "it_IT": "Indica il volo di ritorno",
    },
}


@openupgrade.migrate()
def migrate(env, version):
    # The outbound and the return flights each have their task now: the
    # flight details task becomes the outbound one.
    for xmlid, names in NAMES.items():
        task = env.ref(f"website_switzerland.{xmlid}")
        for lang, name in names.items():
            task.with_context(lang=lang).name = name

    # In SQL: ticking the tasks must not move the registrations nor send mails.
    params = {
        "outbound": env.ref("website_switzerland.task_flight_details").id,
        "return": env.ref("website_switzerland.task_return_flight").id,
    }
    # Before the outbound task is ticked: done before, it had both flights.
    env.cr.execute(
        """
        INSERT INTO event_registration_task_rel (
            task_id, registration_id, sequence, done,
            create_uid, create_date, write_uid, write_date
        )
        SELECT %(return)s, rel.registration_id, rel.sequence,
               COALESCE(rel.done, FALSE) OR EXISTS (
                   SELECT 1 FROM event_flight f
                   WHERE f.registration_id = rel.registration_id
                     AND f.flight_type = 'return'
               ),
               1, NOW() AT TIME ZONE 'UTC', 1, NOW() AT TIME ZONE 'UTC'
        FROM event_registration_task_rel rel
        WHERE rel.task_id = %(outbound)s
        ON CONFLICT (task_id, registration_id) DO NOTHING
        """,
        params,
    )
    _logger.info("Return flight task added to %s registrations", env.cr.rowcount)
    env.cr.execute(
        """
        UPDATE event_registration_task_rel rel SET done = TRUE
        WHERE rel.task_id = %(outbound)s
          AND NOT COALESCE(rel.done, FALSE)
          AND EXISTS (
              SELECT 1 FROM event_flight f
              WHERE f.registration_id = rel.registration_id
                AND f.flight_type = 'outbound'
          )
        """,
        params,
    )
    _logger.info("Outbound flight task ticked for %s registrations", env.cr.rowcount)
