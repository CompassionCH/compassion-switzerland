import json
import logging
import pathlib
import re

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

BODIES = pathlib.Path(__file__).parent / "bodies"

# Taken from the compassion_18 migration run, which converted them correctly
SUBJECTS = {
    "group_visit_step2_email": {
        "fr_CH": "Votre voyage Impact {{object.get_objects().compassion_event_id."
        "country_id.in_preposition}} {{object.get_objects().compassion_event_id."
        "country_id.name}} avec Compassion",
        "de_DE": '{{"Eure" if object.partner_id.plural else "Deine"}} Reise nach '
        "{{object.get_objects().compassion_event_id.country_id.name}} mit Compassion",
    },
}


def _fix_subject(subject):
    """Convert the Jinja leftovers of the v14 subjects."""
    subject = re.sub(r"\$\{\s*(.*?)\s*\}", r"{{\1}}", subject)
    subject = re.sub(
        r"\b(?:objet|oggetto)\.get_(?:objects|oggetti)\(\)",
        "object.get_objects()",
        subject,
    )
    return subject.replace("country_id.preposition", "country_id.in_preposition")


def _repair_template(env, xmlid):
    template = env.ref(f"website_switzerland.{xmlid}", raise_if_not_found=False)
    if not template:
        return
    env.cr.execute(
        "SELECT body_html, subject FROM mail_template WHERE id = %s", [template.id]
    )
    body, subject = env.cr.fetchone()
    body = body or {}
    for file in BODIES.glob(f"{xmlid}.*.html"):
        lang = file.name.removeprefix(f"{xmlid}.").removesuffix(".html")
        body[lang] = file.read_text()
    subject = {lang: _fix_subject(value) for lang, value in (subject or {}).items()}
    subject.update(SUBJECTS.get(xmlid, {}))
    openupgrade.logged_query(
        env.cr,
        "UPDATE mail_template SET body_html = %s, subject = %s WHERE id = %s",
        (json.dumps(body), json.dumps(subject), template.id),
    )


@openupgrade.migrate()
def migrate(env, version):
    """Repair the group visit e-mails (T3523).

    The v14 conversion left Jinja in most translations, links to v10 routes
    (/event/<uuid>/...) and, because of a cached env.ref() in 18.0.1.0.4, the
    step1 text on the step2 template while step1 kept a body that fails to
    render. The repaired bodies are in the bodies/ folder, one per language.
    It also puts back the trip registrations stuck in a Muskathlon stage and
    reactivates the participant task forms and cart picture.
    """
    xmlids = sorted({f.name.split(".")[0] for f in BODIES.glob("*.html")})
    for xmlid in xmlids:
        _repair_template(env, xmlid)
    env["mail.template"].invalidate_model(["body_html", "subject"])
    _logger.info("Repaired %s group visit e-mail templates", len(xmlids))

    # Paying the fee moved trip registrations to the Muskathlon stage
    # "Downpayment paid", outside of their journey: they wait for the
    # confirmation in "Down payment".
    down_payment = env.ref("website_switzerland.stage_group_pay")
    shared = [
        env.ref(f"website_event_compassion.stage_all_{name}").id
        for name in ("confirmed", "attended", "cancelled")
    ]
    lost = (
        env["event.registration"]
        .search(
            [
                ("event_id.event_type_id", "in", down_payment.event_type_ids.ids),
                ("state", "in", ("draft", "open")),
                ("stage_id", "!=", False),
                ("stage_id", "not in", shared),
            ]
        )
        .filtered(lambda reg: reg.event_type_id not in reg.stage_id.event_type_ids)
    )
    if lost:
        lost.write({"stage_id": down_payment.id})
        _logger.info("Moved registrations %s back to Down payment", lost.ids)

    # The v14 migration left these views inactive: the "Sign travel agreement"
    # page of My events was empty and the cart had no participant picture.
    for xmlid in (
        "my_event_include_forms",
        "travel_agreement",
        "cart_participant_picture",
    ):
        view = env.ref(f"website_switzerland.{xmlid}", raise_if_not_found=False)
        if view and not view.active:
            view.active = True
            _logger.info("Reactivated view website_switzerland.%s", xmlid)
