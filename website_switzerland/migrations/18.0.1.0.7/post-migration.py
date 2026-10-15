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
    """
    xmlids = sorted({f.name.split(".")[0] for f in BODIES.glob("*.html")})
    for xmlid in xmlids:
        _repair_template(env, xmlid)
    env["mail.template"].invalidate_model(["body_html", "subject"])
    _logger.info("Repaired %s group visit e-mail templates", len(xmlids))
