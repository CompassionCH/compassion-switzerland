import logging

from openupgradelib import openupgrade

from odoo import fields

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    # Migration 18.0.1.0.10 moved the participants waiting for their agreements
    # to Fill documents in SQL: they lack the tasks of that stage (medical
    # survey and discharge) and their medical survey, so they could leave the
    # stage without them.
    stage = env.ref("website_switzerland.stage_group_medical")
    registrations = env["event.registration"].search(
        [
            (
                "event_id.event_type_id",
                "=",
                env.ref("website_switzerland.event_type_group_visit").id,
            ),
            ("event_id.date_end", ">=", fields.Datetime.now()),
            ("stage_id", "=", stage.id),
            ("state", "not in", ("cancel", "done")),
        ]
    )
    for registration in registrations:
        missing = stage.task_ids - registration.task_ids.task_id
        # In SQL: adding the tasks must not move the registration nor send
        # the mails of the stage again.
        for task in missing:
            env.cr.execute(
                """
                INSERT INTO event_registration_task_rel (
                    task_id, registration_id, sequence, done,
                    create_uid, create_date, write_uid, write_date
                )
                VALUES (
                    %s, %s, %s, FALSE,
                    1, NOW() AT TIME ZONE 'UTC', 1, NOW() AT TIME ZONE 'UTC'
                )
                ON CONFLICT (task_id, registration_id) DO NOTHING
                """,
                (task.id, registration.id, task.sequence),
            )
        if missing:
            _logger.info(
                "Registration %s gets the tasks %s", registration.id, missing.ids
            )
        registration.create_medical_survey()
    env["event.registration"].invalidate_model(["task_ids"])
