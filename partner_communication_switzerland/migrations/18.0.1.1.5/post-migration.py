import html
import json
import logging
import re

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

# The CSP (survival sponsorship) email templates only exist in the database
# (no xmlid). Their v14 Jinja texts were converted to QWeb during the
# migration, but some Jinja syntax was left behind, so most of them fail to
# render (or show raw "% endif" text) in French, German and Italian.
TEMPLATE_NAMES = (
    "CSP Onboarding - Welcome and payment information",
    "CSP Onboarding - Magazine and photo",
    "CSP Onboarding - Vision",
    "CSP Onboarding - Mother's day",
    "CSP Onboarding - Promoter",
    "CSP Onboarding - Vision one year",
    "CSP Onboarding - Call to continue",
    "CSP Onboarding - Continue yes",
    "CSP Onboarding - Continue no",
    "CSP Reminder 1",
    "CSP Reminder 2",
    "CSP Yearly payment slips",
)

# Jinja filter left in an expression: 'X | join("")' is evaluated as Python,
# where join is undefined -> "'NoneType' object is not callable".
JOIN_RE = re.compile(r"([\w.]+\(&quot;[^&]*&quot;\))\s*\|\s*join\(&quot;&quot;\)")
# Jinja statements that were never converted to QWeb tags.
PCT_ENDIF_RE = re.compile(r"(?m)^([ \t]*)%\s*endif\s*")
PCT_ELSE_RE = re.compile(r"(?m)^([ \t]*)%\s*else:?\s*$")
PCT_SET_RE = re.compile(r"(?m)^([ \t]*)%\s*set\s+(\w+)\s*=\s*(.*?)\s*$")

# Jinja namespace() accumulator loop (CSP Yearly payment slips): namespace
# does not exist in QWeb, and a t-set inside a t-foreach does not leak out of
# the loop anyway, so compute the recordset in one expression instead.
NS_SET_RE = re.compile(
    r"(?m)^[ \t]*<t t-set=\"ns\" "
    r"t-value=\"namespace\(correspondents = [^\"]*\"/>[ \t]*\n"
)
NS_LOOP_RE = re.compile(
    r"(?P<indent>[ \t]*)<t t-foreach=\"sponsorships\" t-as=\"s\">\s*"
    r"<t t-set=\"gp\" t-value=\"s\.mapped\(s\.send_gifts_to\)\"/>\s*"
    r"<t t-if=\"gp == partner\">\s*"
    r"%\s*set ns\.correspondents = ns\.correspondents \+ s\s*"
    r"</t>\s*</t>"
)
NS_LOOP_NEW = (
    r'\g<indent><t t-set="correspondents" t-value="sponsorships.filtered('
    r'lambda s: s.mapped(s.send_gifts_to) == partner)"/>'
)

# (template name, language) -> [(broken, fixed)] for one-off breakages
SPECIFIC = {
    # non-ASCII variable names are not allowed in t-set
    ("CSP Onboarding - Magazine and photo", "de_DE"): [
        (
            "% set hängst = 'hängt'",
            '<t t-set="haengst" t-value="&#x27;hängt&#x27;"/>',
        ),
        (
            "% set hängst = 'hängst'",
            '<t t-set="haengst" t-value="&#x27;hängst&#x27;"/>',
        ),
        ('<t t-out="hängst"></t>', '<t t-out="haengst"></t>'),
    ],
    # "#{{" is read as the start of a #{...} placeholder by t-attf
    ("CSP Onboarding - Call to continue", "fr_CH"): [
        (
            't-attf-href="http://compassion.ch/mamans#{{country}}"',
            't-att-href="&#x27;http://compassion.ch/mamans#&#x27; + country"',
        ),
    ],
    # string literal split over two lines
    ("CSP Onboarding - Continue no", "fr_CH"): [
        ("&quot;maman et son\n        bébé&quot;", "&quot;maman et son bébé&quot;"),
    ],
    # unbalanced parenthesis, and contract_lines is never defined
    ("CSP Reminder 1", "it_IT"): [
        (
            "int(sum(contract_lines.filtered("
            "&quot;product_id.survival_sponsorship_sale&quot;)"
            ".mapped(&quot;quantity&quot;))",
            "sum(contracts.mapped(&quot;contract_line_ids&quot;).filtered("
            "&quot;product_id.survival_sponsorship_sale&quot;)"
            ".mapped(&quot;quantity&quot;))",
        ),
    ],
}


# Known breakages that should be gone after the repair. If a stored text
# differs from what the repairs expect, they don't match: report it instead
# of silently leaving the template broken.
LEFTOVER_RE = re.compile(
    r"\|\s*join\(|(?m:^[ \t]*%\s*(?:end)?(?:if|else|elif|set|for)\b)|namespace\("
    r"|int\(sum\(contract_lines|#\{\{|t-out=\"hängst\""
)


def _set(match):
    expr = html.escape(html.unescape(match[3]), quote=True)
    return f'{match[1]}<t t-set="{match[2]}" t-value="{expr}"/>'


def _fix_body(body, name, lang):
    if not body:
        return body
    for old, new in SPECIFIC.get((name, lang), []):
        body = body.replace(old, new)
    body, replaced_loops = NS_LOOP_RE.subn(NS_LOOP_NEW, body)
    if replaced_loops:
        # Only drop the namespace once its loop is gone, otherwise
        # "correspondents" would be used without being defined.
        body = NS_SET_RE.sub("", body)
        body = body.replace("ns.correspondents", "correspondents")
    body = JOIN_RE.sub(r"&quot;&quot;.join(\1)", body)
    body = PCT_ENDIF_RE.sub(r"\1</t>", body)
    body = PCT_ELSE_RE.sub(r'\1</t>\n\1<t t-else="">', body)
    body = PCT_SET_RE.sub(_set, body)
    return body


@openupgrade.migrate()
def migrate(env, version):
    env.cr.execute(
        "SELECT id, name->>'en_US', body_html FROM mail_template "
        "WHERE name->>'en_US' IN %s",
        (TEMPLATE_NAMES,),
    )
    for template_id, name, body_html in env.cr.fetchall():
        if not body_html:
            continue
        fixed = {lang: _fix_body(body, name, lang) for lang, body in body_html.items()}
        changed = [lang for lang in fixed if fixed[lang] != body_html[lang]]
        for lang, body in fixed.items():
            leftovers = sorted(set(LEFTOVER_RE.findall(body or "")))
            if leftovers:
                _logger.warning(
                    "%s (mail.template %s, %s): Jinja leftovers could not be "
                    "fixed automatically, please check: %s",
                    name,
                    template_id,
                    lang,
                    ", ".join(leftover.strip() for leftover in leftovers),
                )
        if not changed:
            continue
        env.cr.execute(
            "UPDATE mail_template SET body_html = %s WHERE id = %s",
            (json.dumps(fixed), template_id),
        )
        _logger.info(
            "%s (mail.template %s): fixed Jinja leftovers for languages: %s",
            name,
            template_id,
            ", ".join(changed),
        )
