import json
import logging
import re

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

# T3503: these texts read the gender of all the children of the letter, which
# fails for sponsors of several children ("Expected singleton"). On v18 such a
# failing letter is rendered again at each flush, which made the monthly
# reminders job too slow to ever finish. Some texts also kept Jinja syntax
# from v14: a "% endif" instead of the closing </t> of their last block, or a
# "|replace" filter that fails in a QWeb expression.
TEMPLATE_NAMES = (
    "Sponsorship Reminder 1",
    "Sponsorship Waiting Reminder 1",
    "Sponsorship Waiting Reminder 2",
    "Sponsorship Waiting Reminder 3",
    "Sponsorship - Birthday Reminder",
    "W&P Journey - Letter writing reminder",
)

# Fixes of single mistakes, applied before the generic ones
SPECIFIC = {
    # plural for several children
    ("Sponsorship Reminder 1", "fr_CH"): [
        (
            "'le' if children.gender == 'M' else 'la'",
            "'les' if len(children) > 1 "
            "else ('le' if children.gender == 'M' else 'la')",
        ),
    ],
    ("Sponsorship Waiting Reminder 2", "de_DE"): [
        (
            "&#x27;seine&#x27; if children.gender == &#x27;M&#x27; "
            "else &#x27;ihre&#x27;",
            "&#x27;seine&#x27; if len(children) == 1 and children.gender == "
            "&#x27;M&#x27; else &#x27;ihre&#x27;",
        ),
        # Jinja filter left in the expression
        (
            "(sum(sponsorships.mapped(&#x27;total_amount&#x27;)) * "
            "min(sponsorships.mapped(&#x27;group_id.advance_billing_months&#x27;)))"
            "|replace(&#x27;.0&#x27;,&#x27;.-&#x27;)",
            "str(sum(sponsorships.mapped(&#x27;total_amount&#x27;)) * "
            "min(sponsorships.mapped(&#x27;group_id.advance_billing_months&#x27;)))"
            ".replace(&#x27;.0&#x27;, &#x27;.-&#x27;)",
        ),
        # unclosed comment ("-->" escaped): hides the whole rest of the letter
        (
            '<!--    <t t-set="extension" '
            't-value="children[0].hold_id.no_money_extension_duration --&gt;"/>\n',
            "",
        ),
    ],
}
# Texts written for a single child: use the gender of the first one
GENDER_RE = re.compile(r"\bchildren\.gender\b")
ENDIF_RE = re.compile(r"\s*%\s*endif\s*</body>")
# ${"{:.0f}".format(amount)} cut in two by the conversion
FORMAT_RE = re.compile(r'<t t-out="&quot;\{:\.0f"></t>"\.format\((\w+)\)\}')
# A Python expression cannot span lines inside a QWeb attribute
MULTILINE_ATTR_RE = re.compile(r'(t-(?:value|if|elif|out|foreach)="[^"]*\n[^"]*")')
# Jinja filter left in an expression: amount|replace('.0','.-')
REPLACE_RE = re.compile(r"\b([a-z_][\w.]*)\|replace\(")


def _fix_body(body, name, lang):
    for old, new in SPECIFIC.get((name, lang), []):
        body = body.replace(old, new)
    body = GENDER_RE.sub("children[:1].gender", body)
    body = REPLACE_RE.sub(r"str(\1).replace(", body)
    body = FORMAT_RE.sub(r'<t t-out="&quot;{:.0f}&quot;.format(\1)"/>', body)
    body = MULTILINE_ATTR_RE.sub(lambda m: re.sub(r"\s*\n\s*", " ", m[1]), body)
    return ENDIF_RE.sub("\n</t></body>", body)


def _leftover(body, name, lang):
    return re.search(r"%\s*endif|\|replace\(|&quot;\{:\.0f\"", body) or any(
        old in body for old, _new in SPECIFIC.get((name, lang), [])
    )


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
            fixed[lang] = body and _fix_body(body, name, lang)
            if fixed[lang] != body:
                changed.append(lang)
            if fixed[lang] and _leftover(fixed[lang], name, lang):
                _logger.warning(
                    "%s (mail.template %s, %s): leftover not fixed, please check it",
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
            "%s (mail.template %s): fixed languages %s",
            name,
            template_id,
            ", ".join(changed),
        )
    env["mail.template"].invalidate_model(["body_html"])
