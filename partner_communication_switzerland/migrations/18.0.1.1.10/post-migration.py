import html
import json
import logging
import re

from lxml import html as lxml_html
from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

# The v14 -> v18 conversion of the e-mail texts skipped some Jinja lines
# ("% set", "% if", "% else", "% endif"): QWeb prints them as text and the
# variables they define stay empty. Some texts also never compiled in v18.
# The texts only exist in the database. Only the most used ones are fixed.
TEMPLATE_NAMES = (
    "Donation - Food crisis",
    "Donation - Food crisis Tanzania 2",
    "Donation - Survival Campaign",
    "Donation - Christmas",
    "Donation - Wash Campaign",
    "Donation - Tanzania Toilets",
    "Donation - Vocational Training Burkina Faso",
    "2608VOC_donation_thankyou",
    "Easter 2026 Donation Thank You",
    "Christmas Gift Fund",
    "CSP Engagement",
    "B2S New letter",
    "B2S Old letter published",
    "B2S Final Letter",
    "B2S e-mail not read",
)
JINJA_RE = re.compile(r"^([ \t]*)%[ \t]*(set|if|else|endif)\b:?(.*?):?[ \t]*$", re.M)
# Expressions that do not compile in v18
REPLACEMENTS = [
    # QWeb variable names must be ASCII
    ('t-set="erfährst"', 't-set="erfaehrst"'),
    ('t-out="erfährst"', 't-out="erfaehrst"'),
    # Python 3 refuses leading zeros
    ("datetime.date(2024,08,17)", "datetime.date(2024,8,17)"),
    ("datetime.date(2022,4,03)", "datetime.date(2022,4,3)"),
    # Jinja accepted an "if" without "else"
    ('&#x27;te&#x27; if plural"', '&#x27;te&#x27; if plural else &#x27;&#x27;"'),
    # a string cannot span two lines
    ("&quot;sind\n        die Briefe&quot;", "&quot;sind die Briefe&quot;"),
    ("&#x27;d&#x27;un enfant&#x27;", "&quot;d&#x27;un enfant&quot;"),
]


def _to_qweb(match):
    indent, keyword, rest = match[1], match[2], match[3].strip()
    expr = html.escape(html.unescape(rest), quote=True)
    if keyword == "set":
        name, value = (part.strip() for part in expr.split("=", 1))
        return f'{indent}<t t-set="{name}" t-value="{value}"/>'
    if keyword == "if":
        return f'{indent}<t t-if="{expr}">'
    if keyword == "else":
        return f'{indent}</t><t t-else="">'
    # "% endif</body>": keep what follows
    return f"{indent}</t>{rest}"


def _fix(body):
    body = JINJA_RE.sub(_to_qweb, body)
    for old, new in REPLACEMENTS:
        body = body.replace(old, new)
    return body


def _compiles(env, body):
    try:
        env["ir.qweb"]._render(
            lxml_html.fragment_fromstring(body, create_parent="div"), {}
        )
    except Exception as error:
        # Without data the rendering fails anyway, only compilation matters
        return "compil" not in str(error).lower()
    return True


@openupgrade.migrate()
def migrate(env, version):
    env.cr.execute(
        "SELECT id, name->>'en_US', body_html FROM mail_template "
        "WHERE name->>'en_US' IN %s",
        (TEMPLATE_NAMES,),
    )
    for template_id, name, body_html in env.cr.fetchall():
        changed = []
        for lang, body in body_html.items():
            # Texts that already work are left untouched
            if not body or (not JINJA_RE.search(body) and _compiles(env, body)):
                continue
            new = _fix(body)
            if JINJA_RE.search(new) or not _compiles(env, new):
                _logger.warning(
                    "%s (mail.template %s, %s): not fixed, please check it",
                    name,
                    template_id,
                    lang,
                )
                continue
            body_html[lang] = new
            changed.append(lang)
        if changed:
            env.cr.execute(
                "UPDATE mail_template SET body_html = %s WHERE id = %s",
                (json.dumps(body_html), template_id),
            )
            _logger.info("%s: fixed languages %s", name, ", ".join(changed))
    env["mail.template"].invalidate_model(["body_html"])
