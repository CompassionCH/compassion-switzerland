import html
import json
import logging
import os
import re
from html.parser import HTMLParser

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

# T3498: the sponsorship communications tested from the "Generate
# communications" wizard. Their texts only live in the database. Several
# translations were never converted from the v14 Jinja syntax to QWeb (raw
# "% set ..." / "${...}" sent to sponsors) or were converted with mistakes that
# prevent the communication from being generated at all. The texts are fixed
# where they stand, so that later edits made in the database are kept.
TEMPLATES = (
    "partner_communication_compassion.email_birthdate",
    "partner_communication_compassion.email_disability",
    "partner_communication_compassion.email_name",
    "partner_communication_compassion.email_gender",
    "partner_communication_compassion.email_parent_alive",
    "partner_communication_compassion.email_multiple_changes",
    "partner_communication_compassion.email_child_planned_exit",
    "partner_communication_compassion.email_child_unplanned_exit",
    "partner_communication_compassion.email_child_notes",
    "partner_communication_compassion.email_disaster_alert",
    "partner_communication_compassion.email_sponsorship_cancellation",
    "partner_communication_compassion.email_project_suspension",
    "partner_communication_switzerland.email_sponsorship_sub_dossier_new",
    "partner_communication_switzerland.email_sponsorship_no_sub",
    "partner_communication_switzerland.email_sub_accept",
    "partner_communication_switzerland.mail_onboarding_sponsorship_confirmation",
    "partner_communication_switzerland.mail_onboarding_step1",
    "partner_communication_switzerland.mail_onboarding_step2",
    "partner_communication_switzerland.mail_onboarding_step3",
    "partner_communication_switzerland.mail_onboarding_step4",
    "partner_communication_switzerland.mail_onboarding_step5",
)

# Translations that hold the wrong text (Italian text in the German version,
# subject and body swapped): restored from the v14 texts, converted to QWeb.
RESTORED_BODIES = {
    ("partner_communication_switzerland.email_sponsorship_no_sub", "de_DE"),
    ("partner_communication_switzerland.email_sub_accept", "de_DE"),
    ("partner_communication_switzerland.email_sub_accept", "it_IT"),
}
RESTORED_SUBJECTS = {
    ("partner_communication_switzerland.email_sponsorship_no_sub", "de_DE"): (
        'Danke, dass {{ "ihr" if (object.partner_id.title.plural or '
        'object.partner_id.title.id == 29) else "du" }} bis jetzt ein Kind '
        'unterstützt {{ "habt" if (object.partner_id.title.plural or '
        'object.partner_id.title.id == 29) else "hast" }}'
    ),
    ("partner_communication_switzerland.email_sub_accept", "de_DE"): (
        '{{ "Eure" if (object.partner_id.title.plural or '
        'object.partner_id.title.id == 29) else "Deine" }} neue '
        '{{ object.get_objects().mapped("child_id").get("Patenschaft") }} für '
        "{{ object.get_objects().mapped(\"child_id\").get_list('preferred_name', 3, "
        "'eure Patenkinder' if (object.partner_id.title.plural or "
        "object.partner_id.title.id == 29) else 'deine Patenkinder', False) }}"
    ),
    ("partner_communication_switzerland.email_sub_accept", "it_IT"): (
        'Il {{ "vostro" if object.partner_id.title.plural or '
        'object.partner_id.title.id == 29 else "tuo" }} nuovo sostegno per '
        '{{ object.get_objects().mapped("child_id").get_list("preferred_name", '
        "translate=False) }}"
    ),
}
RESTORED_DIR = os.path.join(os.path.dirname(__file__), "restored_texts")

# Fixes of single mistakes, applied before the generic conversion.
PLURAL = "(object.partner_id.title.plural or object.partner_id.title.id == 29)"
SPECIFIC = {
    # Birthdate: the old values of all revisions were joined together
    # ("2019-10-01 and Preschool 2") then read as a date.
    ("partner_communication_compassion.email_birthdate", None): [
        ("get_date(&#x27;old_values&#x27;", "get_date(&#x27;old_birthdate&#x27;"),
        ("get_date(&quot;old_values&quot;", "get_date(&quot;old_birthdate&quot;"),
        ("get_date('old_values'", "get_date('old_birthdate'"),
    ],
    ("partner_communication_compassion.email_name", "en_US"): [
        ("object.succes_sentence or &#x27;&#x27;", "&#x27;&#x27;"),
    ],
    # Subject: assignment inside an expression
    ("partner_communication_compassion.email_gender", "de_DE"): [
        (
            "(plural = object.partner_id.title.plural or "
            "object.partner_id.title.id == 29)",
            PLURAL,
        ),
    ],
    # Subject: undefined variable "deiner"
    ("partner_communication_compassion.email_child_planned_exit", "de_DE"): [
        (
            "{{object.partner_id.get('deiner')}}",
            f"{{{{'eurer' if {PLURAL} else 'deiner'}}}}",
        ),
        (
            "(deiner + ' Patenkinder')",
            f"('eurer Patenkinder' if {PLURAL} else 'deiner Patenkinder')",
        ),
    ],
    ("partner_communication_compassion.email_project_suspension", "it_IT"): [
        ("child.Gender", "child.gender"),
    ],
    # Debug list of the suspension reasons ("Internal notes to be removed")
    # sent to sponsors, using an undefined variable.
    ("partner_communication_compassion.email_project_suspension", "de_DE"): [
        (
            re.compile(
                r'<t t-if="reasons">\s*<p><b>Internal notes to be removed</b></p>'
                r".*?</ul>\s*% endif",
                re.S,
            ),
            "",
        ),
    ],
    # A paragraph split inside the if/else blocks: the t-else is no longer
    # next to its t-if once the HTML is parsed.
    ("partner_communication_compassion.email_disaster_alert", "fr_CH"): [
        (
            re.compile(r'(\.)\n([ \t]*)<t t-if="healthy">\n([ \t]*)</p><p>'),
            r'\1</p>\n\2<p><t t-if="healthy">\n\3',
        ),
        (
            re.compile(r'<t t-if="healthy">\n([ \t]*)<p>'),
            r'<p><t t-if="healthy">\n\1',
        ),
        (re.compile(r'<t t-else="">\n([ \t]*)</p><p>'), r'<t t-else="">\n\1'),
        (re.compile(r"(fournitures scolaires\.?)</p>"), r"\1"),
        (
            re.compile(r"(maison est intacte\.\n[ \t]*</t>)(?!\n[ \t]*</p>)"),
            r"\1\n    </p>",
        ),
    ],
    ("partner_communication_compassion.email_sponsorship_cancellation", "de_DE"): [
        (
            re.compile(r'<p>\n([ \t]*)(<t t-if="7 in sponsorships[^"]*">)'),
            r"\1\2\n<p>",
        ),
    ],
    ("partner_communication_switzerland.mail_onboarding_step3", "en_US"): [
        (
            '&#x27;ren&#x27; if not one_child"',
            '&#x27;ren&#x27; if not one_child else &#x27;&#x27;"',
        ),
    ],
    # Onboarding step 4: "letter" does not exist for a sponsorship.
    ("partner_communication_switzerland.mail_onboarding_step4", None): [
        (
            "letter.mapped(&#x27;child_id.field_office_id&#x27;).ids",
            "child.mapped(&#x27;field_office_id&#x27;).ids",
        ),
        (
            '&#x27;ren&#x27; if not one_child"',
            '&#x27;ren&#x27; if not one_child else &#x27;&#x27;"',
        ),
        # namespace() loop to find a country with special letter rules
        (
            "% set restricted = namespace(field=False)",
            "% set restricted_field = ([f.country_id.name for f in "
            "child.mapped('field_office_id') if f.id in (1, 19)] or [False])[-1]",
        ),
        ("restricted.field", "restricted_field"),
    ],
    # Dead "% if False:" block spanning several HTML elements
    ("partner_communication_switzerland.mail_onboarding_step1", "it_IT"): [
        (re.compile(r"<p>\s*% if False:.*?% endif[ \t]*\n", re.S), ""),
    ],
    # Non-ASCII QWeb variable name
    ("partner_communication_compassion.email_child_unplanned_exit", "de_DE"): [
        ("wünschst", "wuenschst"),
    ],
}

# The namespace() loop body becomes useless once restricted_field is computed.
NS_LOOP_RE = re.compile(
    r"% for field in child\.mapped\('field_office_id'\):\s*% if field\.id in "
    r"\(1,\s*19\):\s*% set restricted_field = field\.country_id\.name\s*% endif\s*"
    r"% endfor\s*"
)
STATEMENT_RE = re.compile(
    r"^(?P<indent>[ \t]*)%[ \t]*(?P<kw>set|if|elif|else|endif|for|endfor)\b"
    r"(?P<rest>.*?)[ \t]*$"
)
# "% endif</body>": statement glued to a closing tag
GLUED_STATEMENT_RE = re.compile(
    r"^([ \t]*%[ \t]*(?:endif|endfor|else)\b:?)[ \t]*(<.*)$"
)
EXPR_RE = re.compile(r"\$\{(?P<expr>(?:[^{}]|\{[^{}]*\})*)\}")
TAG_WITH_EXPR_RE = re.compile(r"<[a-zA-Z][^<>]*\$\{[^<>]*>")
ATTR_WITH_EXPR_RE = re.compile(r'(?P<name>[\w:-]+)="(?P<value>[^"]*\$\{[^"]*)"')
FILTER_RE = re.compile(r"\|\s*(?P<name>[a-z_]+)\s*(?:\((?P<args>[^()]*)\))?\s*$")
SIMPLE_FILTERS = {
    "lower": "{}.lower()",
    "upper": "{}.upper()",
    "capitalize": "{}.capitalize()",
    "title": "{}.title()",
    "int": "int({})",
    "string": "str({})",
    "trim": "{}.strip()",
    "length": "len({})",
}
# Jinja filters left in QWeb expressions: 'reason.value|lower'
QWEB_ATTR_RE = re.compile(
    r'(?P<attr>t-(?:value|if|elif|out|foreach))="(?P<expr>[^"]*\|[^"]*)"'
)
SNIPPET_STRIPTAGS_RE = re.compile(
    r"get_snippet\((?P<args>[^()]*)\)\s*\|\s*striptags(?:\s*\|\s*safe)?"
)
# ${"{:,}".format(x).replace(",","'")} cut in two by a previous conversion
THOUSANDS_RE = re.compile(
    r'<t t-out="&quot;\{:,"></t>"\.format\((?P<var>\w+)\)\.replace\(","\s*,\s*"\'"\)\}'
)
THOUSANDS_NEW = (
    r'<t t-out="&quot;{:,}&quot;.format(\g<var>)'
    r'.replace(&quot;,&quot;, &quot;&#x27;&quot;)"/>'
)
SHORT_SIGNATURE_RE = re.compile(
    r'<t t-out="object\.user_id\.short_signature"\s*(?:/>|></t>)'
)
SIGNATURE = (
    "<t t-if=\"object.send_mode != 'physical'\">"
    '<t t-out="object.user_id.signature"/></t>'
)
SIGNATURE_OR_SHORT = (
    SIGNATURE + '<t t-else=""><t t-out="object.user_id.short_signature"/></t>'
)
FONT_STYLE = (
    'font-size:13px;font-family:"Lucida Grande", Helvetica, Verdana, Arial, sans-serif;'
)
FONT_WRAPPER = '<div class="communication-text" t-att-style="{}">'.format(
    html.escape(
        f"{FONT_STYLE!r} if object.send_mode != 'physical' else None", quote=True
    )
)
LEFTOVER_RE = re.compile(
    r"(?m)^[ \t]*%[ \t]*(?:set|if|elif|else|endif|for|endfor)\b|\$\{"
)


class ConversionError(Exception):
    pass


def _inside_string(text, pos):
    quote = None
    for char in text[:pos]:
        if quote:
            if char == quote:
                quote = None
        elif char in "'\"":
            quote = char
    return quote is not None


def _expr(expr, loops=()):
    """Jinja expression -> Python expression (unescaped)."""
    expr = html.unescape(expr).strip()
    expr = SNIPPET_STRIPTAGS_RE.sub(
        lambda m: f"get_snippet({m['args']}, strip_html=True)", expr
    )
    filters = []
    while True:
        match = FILTER_RE.search(expr)
        if not match or _inside_string(expr, match.start()):
            break
        filters.insert(0, (match["name"], match["args"]))
        expr = expr[: match.start()].rstrip()
    for name, args in filters:
        if name in ("safe", "e", "escape"):
            continue
        if name in SIMPLE_FILTERS:
            expr = SIMPLE_FILTERS[name].format(f"({expr})")
        elif name == "join":
            expr = f"({args or repr('')}).join({expr})"
        elif name in ("default", "d"):
            expr = f"(({expr}) or {args})"
        elif name == "replace":
            expr = f"({expr}).replace({args})"
        else:
            raise ConversionError(f"unknown filter |{name} in {expr!r}")
    for var in loops:
        expr = expr.replace("loop.index0", f"{var}_index")
        expr = expr.replace("loop.index", f"({var}_index + 1)")
        expr = expr.replace("loop.first", f"{var}_first")
        expr = expr.replace("loop.last", f"{var}_last")
    if "loop." in expr or " is defined" in expr:
        raise ConversionError(f"unsupported Jinja syntax in {expr!r}")
    # A Python expression cannot span lines inside a QWeb attribute
    return re.sub(r"\s*\n\s*", " ", expr)


def _attr(expr):
    return html.escape(expr, quote=True)


def _convert_line(line, loops):
    def tag_sub(tag_match):
        def attr_sub(match):
            value = EXPR_RE.sub(
                lambda e: "{{ " + _expr(e["expr"], loops) + " }}",
                html.unescape(match["value"]),
            )
            return f't-attf-{match["name"]}="{_attr(value)}"'

        return ATTR_WITH_EXPR_RE.sub(attr_sub, tag_match[0])

    line = TAG_WITH_EXPR_RE.sub(tag_sub, line)
    return EXPR_RE.sub(lambda e: f'<t t-out="{_attr(_expr(e["expr"], loops))}"/>', line)


def _convert_body(body):
    """Convert the Jinja line statements and ${expressions} of a body. Works
    for fully Jinja texts as well as for half converted ones, where a stray
    "% endif" closes a <t t-if> written in QWeb."""
    lines = []
    for line in body.split("\n"):
        glued = GLUED_STATEMENT_RE.match(line)
        lines.extend([glued[1], glued[2]] if glued else [line])
    out, loops = [], []
    for line in lines:
        match = STATEMENT_RE.match(line)
        if not match:
            out.append(_convert_line(line, loops))
            continue
        indent, kw = match["indent"], match["kw"]
        rest = match["rest"].strip().rstrip(":").strip()
        if kw == "set":
            name, sep, value = rest.partition("=")
            if not sep or not name.strip().isidentifier():
                raise ConversionError(f"cannot convert {line.strip()!r}")
            value = _attr(_expr(value, loops))
            out.append(f'{indent}<t t-set="{name.strip()}" t-value="{value}"/>')
        elif kw == "if":
            out.append(f'{indent}<t t-if="{_attr(_expr(rest, loops))}">')
        elif kw == "elif":
            out.append(f'{indent}</t><t t-elif="{_attr(_expr(rest, loops))}">')
        elif kw == "else":
            out.append(f'{indent}</t><t t-else="">')
        elif kw in ("endif", "endfor"):
            if kw == "endfor" and loops:
                loops.pop()
            out.append(f"{indent}</t>")
        elif kw == "for":
            target, sep, iterable = rest.partition(" in ")
            if not sep or not target.strip().isidentifier():
                raise ConversionError(f"cannot convert {line.strip()!r}")
            loops.append(target.strip())
            out.append(
                f'{indent}<t t-foreach="{_attr(_expr(iterable, loops))}" '
                f't-as="{target.strip()}">'
            )
    return "\n".join(out)


def _convert_subject(subject):
    """Jinja subject (may start with "% set" lines) -> inline template."""
    variables, parts = {}, []

    def inline(expr):
        for var, value in variables.items():
            expr = re.sub(rf"\b{var}\b", lambda _m, v=value: v, expr)
        return expr

    for line in subject.split("\n"):
        match = STATEMENT_RE.match(line)
        if match and match["kw"] == "set":
            name, _sep, value = match["rest"].strip().partition("=")
            variables[name.strip()] = f"({inline(_expr(value))})"
        elif match:
            raise ConversionError(f"statement in subject: {line.strip()!r}")
        elif line.strip():
            parts.append(line.strip())
    return EXPR_RE.sub(
        lambda e: "{{ " + inline(_expr(e["expr"])) + " }}", " ".join(parts)
    )


MULTILINE_ATTR_RE = re.compile(r'(t-(?:value|if|elif|out|foreach)="[^"]*\n[^"]*")')


def _fix_qweb_filters(body):
    # A Python expression cannot span lines: 'Wärt ihr' if plural else 'Wärst
    #     du'
    body = MULTILINE_ATTR_RE.sub(lambda m: re.sub(r"\s*\n\s*", " ", m[1]), body)

    def sub(match):
        expr = html.unescape(match["expr"])
        if not FILTER_RE.search(expr) and not SNIPPET_STRIPTAGS_RE.search(expr):
            # "|" used inside the expression (ex: hours_fcp|string > 3)
            expr = re.sub(
                r"(\w[\w.]*)\s*\|\s*(lower|upper|string|int|title|capitalize)\b",
                lambda m: SIMPLE_FILTERS[m[2]].format(m[1]),
                expr,
            )
        else:
            expr = _expr(expr)
        return f'{match["attr"]}="{_attr(expr)}"'

    return QWEB_ATTR_RE.sub(sub, body)


class _BlockChecker(HTMLParser):
    VOID = {"br", "img", "hr", "meta", "input", "link", "col", "wbr", "source"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.errors = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        if not self.stack:
            self.errors.append(f"unexpected </{tag}>")
        elif self.stack[-1] == tag:
            self.stack.pop()
        elif tag == "t" or self.stack[-1] == "t":
            self.errors.append(f"</{tag}> closes <{self.stack[-1]}>")
        elif tag in self.stack:
            while self.stack.pop() != tag:
                pass


def _block_errors(body):
    checker = _BlockChecker()
    checker.feed(body)
    checker.close()
    return checker.errors + [f"unclosed <{tag}>" for tag in checker.stack if tag == "t"]


def _check_blocks(original, body):
    """Refuse a conversion that breaks the nesting of the QWeb blocks. Some
    texts already mix blocks and paragraphs in a way QWeb tolerates, only new
    errors count."""
    errors = _block_errors(body)
    if len(errors) > len(_block_errors(original)):
        raise ConversionError("; ".join(errors[:3]))


def _add_layout(body):
    """Same font as the major revision emails and the full signature of the
    employee in emails (letters keep their layout and short signature)."""
    if 'class="communication-text"' in body:
        return body
    if "object.user_id.signature" not in body:
        if SHORT_SIGNATURE_RE.search(body):
            body = SHORT_SIGNATURE_RE.sub(SIGNATURE_OR_SHORT, body, count=1)
        else:
            body = re.sub(r"(</body>\s*</html>\s*)?$", SIGNATURE + r"\1", body, count=1)
    if "<body>" in body:
        return body.replace("<body>", "<body>" + FONT_WRAPPER, 1).replace(
            "</body>", "</div></body>", 1
        )
    return FONT_WRAPPER + body + "</div>"


def _apply_specific(text, xmlid, lang):
    for key in ((xmlid, None), (xmlid, lang)):
        for old, new in SPECIFIC.get(key, []):
            text = old.sub(new, text) if hasattr(old, "sub") else text.replace(old, new)
    return NS_LOOP_RE.sub("", text)


def _fix_body(body, xmlid, lang):
    # Only while the text is still the broken one (not fixed by hand since)
    if (xmlid, lang) in RESTORED_BODIES and LEFTOVER_RE.search(body or ""):
        name = f"{xmlid.split('.')[1]}_{lang}.html"
        with open(os.path.join(RESTORED_DIR, name)) as restored:
            body = restored.read()
    if not body or not body.strip() or body.strip() == "TODO":
        return body
    original = body
    body = _apply_specific(body, xmlid, lang)
    body = THOUSANDS_RE.sub(THOUSANDS_NEW, body)
    if LEFTOVER_RE.search(body):
        body = _convert_body(body)
    body = _fix_qweb_filters(body)
    _check_blocks(original, body)
    return _add_layout(body)


def _fix_subject(subject, xmlid, lang):
    if (xmlid, lang) in RESTORED_SUBJECTS and LEFTOVER_RE.search(subject or ""):
        return RESTORED_SUBJECTS[(xmlid, lang)]
    if not subject:
        return subject
    subject = _apply_specific(subject, xmlid, lang)
    if LEFTOVER_RE.search(subject):
        subject = _convert_subject(subject)
    return subject


def _fix_field(template_id, xmlid, field, values, fixer):
    fixed, changed = {}, []
    for lang, value in values.items():
        try:
            fixed[lang] = fixer(value, xmlid, lang)
        except ConversionError as error:
            _logger.warning(
                "%s (mail.template %s, %s %s) could not be converted, please "
                "check it: %s",
                xmlid,
                template_id,
                field,
                lang,
                error,
            )
            fixed[lang] = value
        if fixed[lang] != value:
            changed.append(lang)
    return fixed, changed


@openupgrade.migrate()
def migrate(env, version):
    for xmlid in TEMPLATES:
        template = env.ref(xmlid, raise_if_not_found=False)
        if not template:
            continue
        env.cr.execute(
            "SELECT subject, body_html FROM mail_template WHERE id = %s",
            (template.id,),
        )
        subject, body_html = env.cr.fetchone()
        new_subject, subject_langs = _fix_field(
            template.id, xmlid, "subject", subject or {}, _fix_subject
        )
        new_body, body_langs = _fix_field(
            template.id, xmlid, "body", body_html or {}, _fix_body
        )
        if not subject_langs and not body_langs:
            continue
        env.cr.execute(
            "UPDATE mail_template SET subject = %s, body_html = %s WHERE id = %s",
            (json.dumps(new_subject), json.dumps(new_body), template.id),
        )
        _logger.info(
            "%s (mail.template %s): fixed subject %s, body %s",
            xmlid,
            template.id,
            ", ".join(subject_langs) or "-",
            ", ".join(body_langs) or "-",
        )
    env["mail.template"].invalidate_model(["subject", "body_html"])
