import json
import logging
import re

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

# "%  if EXPR:" is a non-standard shorthand that was never converted to a
# real QWeb <t t-if> directive (same class of bug as thankyou_letters, see
# T3315). QWeb only interprets t-* attributes on elements, so this line was
# rendered verbatim as literal code text in the sent email instead of being
# evaluated - the matching closing "</t>" tag further down was already a
# real tag, so only the opening line needs converting.
PRAGMA_IF_RE = re.compile(r"^(?P<indent>[ \t]*)%\s*if\s+(?P<expr>.*):\s*$")

# de_DE-only, unrelated to the "%  if" bug above: a dead "% set könnt = ..."
# pragma line whose variable is never referenced anywhere else in the
# template (the only other occurrence of "könnt" is an unrelated string
# literal used to replace a "[könnt]" placeholder token). Never executed,
# rendered as literal garbage text - just drop it rather than convert it to
# a real but pointless <t t-set>.
DEAD_SET_KOENNT_RE = re.compile(r"(?m)^[ \t]*%\s*set\s+könnt\s*=.*\n")


def _fix_body(body):
    if not body:
        return body
    body = DEAD_SET_KOENNT_RE.sub("", body)
    lines = []
    for line in body.split("\n"):
        match = PRAGMA_IF_RE.match(line)
        if match:
            line = f'{match["indent"]}<t t-if="{match["expr"]}">'
        lines.append(line)
    return "\n".join(lines)


@openupgrade.migrate()
def migrate(env, version):
    template = env.ref(
        "partner_communication_switzerland.mail_onboarding_sponsorship_confirmation"
    )
    env.cr.execute("SELECT body_html FROM mail_template WHERE id = %s", (template.id,))
    (body_html,) = env.cr.fetchone()
    if not body_html:
        return

    fixed = {lang: _fix_body(body) for lang, body in body_html.items()}
    if fixed == body_html:
        _logger.info("mail_onboarding_sponsorship_confirmation: nothing to fix")
        return

    env.cr.execute(
        "UPDATE mail_template SET body_html = %s WHERE id = %s",
        (json.dumps(fixed), template.id),
    )
    _logger.info(
        "mail_onboarding_sponsorship_confirmation: fixed raw pragma lines "
        "for languages: %s",
        ", ".join(lang for lang in fixed if fixed[lang] != body_html.get(lang)),
    )
