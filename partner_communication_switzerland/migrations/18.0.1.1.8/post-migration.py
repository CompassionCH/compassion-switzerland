import json
import logging
import re

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

# T3503: the v18 editor cannot float an image, so the full width photo of the
# CSP reminders can no longer be put next to the text by hand and the letter
# takes two pages. The templates only exist in the database (no xmlid).
TEMPLATE_NAMES = ("CSP Reminder 1", "CSP Reminder 2")
PHOTO_RE = re.compile(r'(<img\s[^>]*t-attf-src="\{\{imglink\}\}"[^>]*?)\s*/?>')
PHOTO_STYLE = "width: 25%; float: right; margin: 0 0 10px 18px;"


def _fix_photo(match):
    tag = re.sub(r'\s(style|class)="[^"]*"', "", match[1])
    return f'{tag} style="{PHOTO_STYLE}"/>'


@openupgrade.migrate()
def migrate(env, version):
    env.cr.execute(
        "SELECT id, name->>'en_US', body_html FROM mail_template "
        "WHERE name->>'en_US' IN %s",
        (TEMPLATE_NAMES,),
    )
    for template_id, name, body_html in env.cr.fetchall():
        fixed, changed = {}, []
        for lang, body in (body_html or {}).items():
            fixed[lang] = body and PHOTO_RE.sub(_fix_photo, body)
            if fixed[lang] != body:
                changed.append(lang)
            elif body and "<img" in body:
                _logger.warning(
                    "%s (mail.template %s, %s): photo not found, please check it",
                    name,
                    template_id,
                    lang,
                )
        if not changed:
            continue
        env.cr.execute(
            "UPDATE mail_template SET body_html = %s WHERE id = %s",
            (json.dumps(fixed), template_id),
        )
        _logger.info(
            "%s (mail.template %s): photo floated for languages: %s",
            name,
            template_id,
            ", ".join(changed),
        )
    env["mail.template"].invalidate_model(["body_html"])
