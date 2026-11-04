import json
import logging
import pathlib

from openupgradelib import openupgrade

from odoo import Command, fields

_logger = logging.getLogger(__name__)

BODIES = pathlib.Path(__file__).parent / "bodies"

# xmlid: (sequence, registration state, set by hand only, names)
STAGES = {
    "website_switzerland.stage_group_pay": (
        10,
        "draft",
        False,
        {
            "en_US": "Unconfirmed",
            "fr_CH": "Non confirmé",
            "de_DE": "Nicht bestätigt",
            "it_IT": "Non confermato",
        },
    ),
    "website_switzerland.stage_group_registered": (
        15,
        "draft",
        False,
        {"fr_CH": "Inscrit", "de_DE": "Angemeldet", "it_IT": "Iscritto"},
    ),
    "website_event_compassion.stage_all_confirmed": (20, "open", False, {}),
    "website_switzerland.stage_group_flights": (
        21,
        None,
        True,
        {"fr_CH": "Vols", "de_DE": "Flüge", "it_IT": "Voli"},
    ),
    "website_switzerland.stage_group_medical": (
        22,
        None,
        False,
        {
            "en_US": "Fill documents",
            "fr_CH": "Remplir les documents",
            "de_DE": "Dokumente ausfüllen",
            "it_IT": "Compilare i documenti",
        },
    ),
    "website_switzerland.stage_group_documents": (
        23,
        None,
        True,
        {
            "en_US": "Payment",
            "fr_CH": "Paiement",
            "de_DE": "Zahlung",
            "it_IT": "Pagamento",
        },
    ),
    "website_switzerland.stage_group_trip_paid": (
        24,
        None,
        False,
        {"fr_CH": "Voyage payé", "de_DE": "Reise bezahlt", "it_IT": "Viaggio pagato"},
    ),
    "website_switzerland.stage_group_unconfirmed": (
        25,
        None,
        False,
        {
            "en_US": "Criminal record",
            "fr_CH": "Casier judiciaire",
            "de_DE": "Strafregisterauszug",
            "it_IT": "Casellario giudiziale",
        },
    ),
    "website_switzerland.stage_group_ready": (
        26,
        None,
        False,
        {
            "en_US": "Ready to fly",
            "fr_CH": "Prêt à partir",
            "de_DE": "Startklar",
            "it_IT": "Pronto a partire",
        },
    ),
    "website_event_compassion.stage_all_staff": (28, None, True, {}),
    "website_event_compassion.stage_all_attended": (30, "done", False, {}),
    "website_event_compassion.stage_all_cancelled": (40, "cancel", False, {}),
}

TASK_STAGES = {
    "task_step1_sent": "website_switzerland.stage_group_pay",
    "task_down_payment": "website_switzerland.stage_group_registered",
    "task_activate_account": "website_event_compassion.stage_all_confirmed",
    "task_flight_details": "website_switzerland.stage_group_flights",
    "task_sign_travel": "website_switzerland.stage_group_medical",
    "task_sign_child_protection": "website_switzerland.stage_group_medical",
    "task_passport": "website_switzerland.stage_group_medical",
    "task_medical_survey": "website_switzerland.stage_group_medical",
    "task_medical_discharge": "website_switzerland.stage_group_medical",
    "task_full_payment": "website_switzerland.stage_group_documents",
    "task_criminal": "website_switzerland.stage_group_unconfirmed",
}

# rule xmlid: stage xmlid, the mail is sent when the stage is reached
STAGE_MAILS = {
    "group_visit_step3_mail": "website_event_compassion.stage_all_confirmed",
    "group_visit_step2_mail": "website_switzerland.stage_group_medical",
    "group_visit_after_trip_feedback_mail": (
        "website_event_compassion.stage_all_attended"
    ),
}

# Configs whose rules changed, to give to the upcoming group visits
SYNCED_CONFIGS = (
    "group_visit_step3_config",
    "group_visit_flights_config",
    "group_visit_step2_config",
    "group_visit_travel_documents_config",
    "group_visit_criminal_record_config",
    "group_visit_after_trip_feedback_config",
    # No longer sent after a stage: it is the reminder sent from the event.
    "group_visit_medical_survey_config",
)


def _ref(env, xmlid):
    if "." not in xmlid:
        xmlid = f"website_switzerland.{xmlid}"
    return env.ref(xmlid)


def _load_texts(env):
    """The texts written for the new order of the stages."""
    subjects = json.loads((BODIES / "subjects.json").read_text())
    for xmlid, subject in subjects.items():
        template = _ref(env, xmlid)
        env.cr.execute(
            "SELECT body_html, subject FROM mail_template WHERE id = %s",
            [template.id],
        )
        old_body, old_subject = env.cr.fetchone()
        body = old_body or {}
        for file in BODIES.glob(f"{xmlid}.*.html"):
            body[file.name.removeprefix(f"{xmlid}.").removesuffix(".html")] = (
                file.read_text()
            )
        openupgrade.logged_query(
            env.cr,
            "UPDATE mail_template SET body_html = %s, subject = %s WHERE id = %s",
            (
                json.dumps(body),
                json.dumps(dict(old_subject or {}, **subject)),
                template.id,
            ),
        )
    env["mail.template"].invalidate_model(["body_html", "subject"])


@openupgrade.migrate()
def migrate(env, version):
    """Give the group visits the stages Unconfirmed, Registered, Confirmed,
    Flights, Fill documents, Payment, Trip paid, Criminal record, Ready to fly,
    Staff, Attended, Cancelled, and their mails (T3523).

    - Unconfirmed: left once the registration confirmation (step1) is sent.
    - Registered: paying the fee confirms the registration and opens the
      MyCompassion account.
    - Flights and Payment are set by hand (Payment by creating the invoice of
      the trip), the other stages are left once their tasks are done.
    - The agreements, the passport and the medical survey are asked together
      in Fill documents, the criminal record last.
    - Attended is set by hand and sends the feedback mail.
    The participants already past a stage don't get its mail late.
    """
    for xmlid, (sequence, state, manual, names) in STAGES.items():
        openupgrade.logged_query(
            env.cr,
            """
            UPDATE event_registration_stage
            SET sequence = %s, registration_state = %s, manual_only = %s,
                name = name || %s::jsonb
            WHERE id = %s
            """,
            (sequence, state, manual, json.dumps(names), _ref(env, xmlid).id),
        )
    env["event.registration.stage"].invalidate_model(
        ["sequence", "registration_state", "manual_only", "name"]
    )
    for task, stage in TASK_STAGES.items():
        _ref(env, task).stage_id = _ref(env, stage)

    group_visit = _ref(env, "event_type_group_visit")
    group_visit.write(
        {
            "stage_ids": [Command.set([_ref(env, xmlid).id for xmlid in STAGES])],
            "reminder_config_id": _ref(env, "group_visit_medical_survey_config").id,
        }
    )

    # The agreements are now asked with the other documents.
    env.cr.execute(
        """
        UPDATE event_registration r SET stage_id = %s
        FROM event_event e
        WHERE e.id = r.event_id AND e.event_type_id = %s AND r.stage_id = %s
        RETURNING r.id
        """,
        (
            _ref(env, "stage_group_medical").id,
            group_visit.id,
            _ref(env, "stage_group_unconfirmed").id,
        ),
    )
    moved = [row[0] for row in env.cr.fetchall()]
    env["event.registration"].invalidate_model(["stage_id"])
    _logger.info("Group visit registrations %s moved to Fill documents", moved)

    for xmlid, stage in STAGE_MAILS.items():
        _ref(env, xmlid).write(
            {
                "interval_type": "after_stage",
                "stage_id": _ref(env, stage).id,
                "interval_unit": "now",
                "interval_nbr": 1,
            }
        )
    survey_invitation = env.ref(
        "website_switzerland.group_visit_medical_survey_mail", raise_if_not_found=False
    )
    if survey_invitation:
        survey_invitation.unlink()
    _ref(
        env, "group_visit_medical_survey_config"
    ).name = "Group visit: missing documents reminder"
    _ref(env, "group_visit_travel_documents_config").send_mode = "auto_digital"
    _load_texts(env)

    configs = env["partner.communication.config"]
    for xmlid in SYNCED_CONFIGS:
        configs |= _ref(env, xmlid)
    events = env["event.event"].search(
        [
            ("event_type_id", "=", group_visit.id),
            ("date_end", ">=", fields.Datetime.now()),
        ]
    )
    events._sync_template_mails(configs)
    _logger.info("Mails of the group visits %s follow the stages", events.ids)

    # Emptied by the Muskathlon migration, nobody uses it any more.
    env.cr.execute(
        """
        SELECT s.id FROM event_registration_stage s
        WHERE s.name->>'en_US' = 'Downpayment paid'
          AND NOT EXISTS (
              SELECT 1 FROM event_registration r WHERE r.stage_id = s.id
          )
          AND NOT EXISTS (
              SELECT 1 FROM ir_model_data d
              WHERE d.model = 'event.registration.stage' AND d.res_id = s.id
          )
        """
    )
    env["event.registration.stage"].browse([r[0] for r in env.cr.fetchall()]).unlink()
