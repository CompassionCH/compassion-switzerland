import ast
import html
import json
import logging
import os
import re
import unicodedata
from html.parser import HTMLParser

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

# T3538: mail templates still holding v14 code that Odoo 18 cannot render.
# Most texts only live in the database (created or translated by hand), so they
# are fixed where they stand, in every active language, keeping later edits:
# - Jinja left over by the migration: "% set/if/for" lines and ${expressions},
#   sent to the recipients as raw text;
# - Jinja-only code in converted texts: namespace(), .iteritems(), loop.index,
#   |filters, "x if y" without else;
# - expressions broken by hand or by machine translation;
# - fields and methods that no longer exist in Odoo 18.
# Only the texts that still hold the faulty code are changed.

LANGS = ("en_US", "fr_CH", "de_DE", "it_IT")

# Templates archived: no communication rule, server action or other record uses
# them, and their text only holds v14 code (id: name, both checked). A template
# still used by an active communication rule is kept.
ARCHIVED = {
    41: "Template for tasks assigned",
    93: "Project Transition",
    100: "Nick Vujicic - New Dossier",
    # Odoo 14 template, no longer in the project module
    106: "project module install then send email",
    118: "Bengladesh Crisis",
    124: "Bengladesh Crisis 2",
    126: "Sponsorship - Welcome Active",
    138: "Christmas Campaign",
    140: "SMS Mass Communication",
    156: "New Dossier - Write&Pray",
    180: "Default",
    198: "Donation - Wash Campaign (Ghana) - XCC",
    241: "Donation - 670km",
    247: "Letter Attachment Delay (coronavirus)",
    248: "Donation - Covid19 Campaign",
    287: "Test Jonathan",
    381: "Lost Letter",
    440: "Sponsorship Activation Reminder 1",
    # Many2Many communications, replaced by Compassion Communities (18.0.1.1.13)
    506: "Many2Many Onboarding - Welcome and payment information",
    507: "Many2Many Onboarding - Stop recurrent donation",
    553: "Golden Tickets : Approval",
    554: "Golden Tickets : Completion",
    555: "Task: Completion",
}
# Odoo templates still holding their Odoo 14 text: reloaded from their module,
# only while a text holds code of the v14 version (edits made since are kept)
RESET = {
    # goals have no name in Odoo 18
    "gamification.email_template_goal_reminder": re.compile(r"\bobject\.name\b"),
    "survey.mail_template_user_input_invite": re.compile(r"\.certificate\b"),
}
# Texts mangled by the migration (or by machine translation in v14), restored
# from the v14 texts in restored_texts/<id>_<lang>.jinja, while they are broken.
RESTORED = {
    (315, "fr_CH"): "Tax Receipt Custom Amount",
    (315, "de_DE"): "Tax Receipt Custom Amount",
    (315, "it_IT"): "Tax Receipt Custom Amount",
    (494, "it_IT"): "Sorry communication",
}
RESTORED_DIR = os.path.join(os.path.dirname(__file__), "restored_texts")

# Fields and methods renamed or removed since v14, in the expressions.
# A removed field Jinja rendered as empty becomes False.
RENAMES = [
    (re.compile(r"\bmove_id\.invoice_type\b"), "move_id.invoice_category"),
    (re.compile(r"\bcompany_id\.address_name\b"), "company_id.commercial_name"),
    (
        re.compile(
            r"""\(\s*['"]has_sponsorships['"]\s*,\s*['"]=['"]\s*,\s*True\s*\)"""
        ),
        "('number_sponsorships', '>', 0)",
    ),
    (re.compile(r"\.has_sponsorships\b"), ".number_sponsorships"),
    # The birthdate was a string in v14
    (
        re.compile(
            r"""\b(partner(?:_id)?)\.birthdate(?:_date)?\s*(>=|<=|>|<|==)\s*"""
            r"""(['"])(\d{4})-(\d{1,2})-(\d{1,2})\3"""
        ),
        lambda m: f"{m[1]}.birthdate_date {m[2]} "
        f"datetime.date({int(m[4])}, {int(m[5])}, {int(m[6])})",
    ),
    (re.compile(r"\b(partner(?:_id)?)\.birthdate\b(?!_)"), r"\1.birthdate_date"),
    # Field that existed neither in v14 nor in v18
    (re.compile(r"\bobject\.event_id\.thank_you_text\b"), "False"),
    # Domain operator escaped twice: '&amp;'
    (re.compile(r"""(['"])&amp;\1"""), r"\1&\1"),
    (
        re.compile(r"""\.thankyou_letter\s*(==|!=)\s*['"]no['"]"""),
        r".thankyou_preference \1 'none'",
    ),
    (re.compile(r"""get_list\((['"])full_name\1"""), r"get_list(\1name\1"),
    (
        re.compile(r"""\((['"])translator_id\1,\s*(['"])=\2,\s*partner\.id\)"""),
        "('new_translator_id.partner_id', '=', partner.id)",
    ),
    (
        re.compile(r"\bpartner_compassion\.partner_segmentation_survey\b"),
        "partner_segmentation.partner_segmentation_survey",
    ),
    (
        re.compile(r"\.payment_type_attachment\b"),
        ".get_payment_type_attachment_string()",
    ),
    (re.compile(r"\b[\w.]*partner(?:_id)?\.send_original\b"), "False"),
    # v18 signup tokens are computed, their validity is no longer stored
    (re.compile(r"\bpartner\.signup_valid and "), ""),
    (
        re.compile(
            r"""\.generate_email\(object\.id,\s*\[(['"])body_html\1\]\)\[\1body_html\1\]"""
        ),
        "._render_field('body_html', object.ids)[object.id]",
    ),
    (re.compile(r"\.browse\(id\.id\)"), ".browse(id)"),
]
# Code translated with the text (Italian): oggetto.soggetto o ''
ITALIAN_CODE = [
    (re.compile(r"\boggetto\b"), "object"),
    (re.compile(r"\.soggetto\b"), ".subject"),
    (re.compile(r"\.nome\b"), ".name"),
    (re.compile(r"(?<=[\w)\]'\"]) o (?=[\w(\['\"])"), " or "),
]
JINJA_LITERALS = re.compile(r"(?<![\w.])(true|false)(?![\w(])")
LOOP_RE = re.compile(r"\bloop\.(index0|index|first|last|length)\b")
LOOP_VARS = {
    "index0": "{}_index",
    "index": "({}_index + 1)",
    "first": "{}_first",
    "last": "{}_last",
    "length": "{}_size",
}

# Fixes of single mistakes, applied before the generic conversion.
# (template id, language or None for all): [(old, new)], old being a string or
# a compiled regex. The name of the template is checked before applying them.
SPECIFIC_NAMES = {
    95: "Event Donation - Thank You Letter",
    96: "Donation - Summary",
    159: "Communication revision reminder",
    207: "App mobile account creation (support answer)",
    194: "Donation - Wash Campaign",
    242: "W&P Journey - Contribution payment reminder",
    274: "Sponsorship Onboarding - First B2S Letter",
    315: "Tax Receipt Custom Amount",
    344: "QR Sponsorship Payment Slips",
    377: "CSP Reminder 2",
    453: "Muskathlon registration confirmation (existing user)",
    458: "Task: Notify blocked",
    459: "Task: notfiy qualification due",
    461: "Task: Notify review due",
    514: "Mass communication (partner based)",
    273: "Sponsorship Onboarding - Zoom Reminder",
    339: "W&P Journey - sponsorship transformation",
    537: "New Applicant (notification)",
}
# The loop over the donors is never closed
DONORS_LOOP_END = (re.compile(r"(</tr>\n)(\s*\n[ \t]*</tbody>)"), r"\1</t>\2")
# The communication is about a Zoom session: the children are the sponsored ones
ZOOM_SPONSORSHIPS = [
    (
        "% set sponsorships = object.get_objects()",
        "% set sponsorships = object.partner_id.sponsorship_ids",
    ),
    (
        '<t t-set="sponsorships" t-value="object.get_objects()"/>',
        '<t t-set="sponsorships" t-value="object.partner_id.sponsorship_ids"/>',
    ),
]
# The reminder paragraph opens its block inside the previous paragraph
REMINDER_BLOCK = [
    (re.compile(r"\n% if reminder:\n</p>\n"), "\n</p>\n% if reminder:\n"),
    (re.compile(r"(\n% if reminder:\n<p>.*\n)% endif\n</p>\n"), r"\1</p>\n% endif\n"),
]
TASK_USER = [(re.compile(r"\bobject\.user_id\b"), "object.user_ids[:1]")]
SPECIFIC = {
    (95, "de_DE"): [("plral", "plural")],
    # The loop over the ambassadors opens inside a paragraph and closes it
    (95, "it_IT"): [
        (
            re.compile(
                r'<p>\n(\s*<t t-foreach="ambassadors\.[^"]*" t-as="amb">\n'
                r'\s*<t t-set="count" t-value="count \+ 1"/>\n\s*)</p>'
            ),
            r"</p>\n\1",
        )
    ],
    (96, "fr_CH"): [DONORS_LOOP_END],
    (96, "it_IT"): [DONORS_LOOP_END],
    # Dead "% if False:" block spanning several paragraphs
    (273, "it_IT"): [
        (re.compile(r"<p>\s*% if False:.*?% endif[ \t]*\n", re.S), ""),
        *ZOOM_SPONSORSHIPS,
    ],
    (273, "de_DE"): ZOOM_SPONSORSHIPS,
    (339, "fr_CH"): REMINDER_BLOCK,
    (339, "de_DE"): REMINDER_BLOCK,
    # Link URL cut by the conversion: '{}'.format() inside {{ }}
    (159, None): [
        (
            re.compile(
                r"\{\{base_url \+ '/web#id=\{\}\}(&amp;view_type=form&amp;model="
                r"partner\.communication\.revision)'\.format\(revision\.id\)\}"
            ),
            r"{{base_url}}/web#id={{revision.id}}\1",
        )
    ],
    # Claim answer: a claim has no send mode (always true in v14)
    (207, None): [("object.send_mode != &#x27;physical&#x27;", "True")],
    # The variables of the donation are only set in the other languages
    (194, "de_DE"): [
        (
            re.compile(
                r'(<t t-set="invoices" t-value="[^"]*"/>)(?!<t t-set="products")'
            ),
            r'\1<t t-set="products" t-value="invoice_lines.mapped('
            r'&#x27;product_id&#x27;)"/>'
            r'<t t-set="gift" t-value="&#x27;gift&#x27; in invoice_lines.mapped('
            r'&#x27;move_id.invoice_category&#x27;)"/>',
        )
    ],
    (242, "en_US"): [("&#x27;done),", "&#x27;done&#x27;),"), ("'done),", "'done'),")],
    # "special" became a boolean, the country name was in special.field
    (274, "fr_CH"): [
        (
            "special.field",
            "([f.country_id.name for f in child.mapped(&#x27;field_office_id&#x27;) "
            "if f.id in (1, 19)] or [False])[-1]",
        )
    ],
    (315, "en_US"): [
        (
            "(&#x27;state&#x27;,&#x27;=&#x27;,&#x27;paid&#x27;)",
            "(&#x27;payment_state&#x27;,&#x27;=&#x27;,&#x27;paid&#x27;)",
        ),
        ("('state','=','paid')", "('payment_state','=','paid')"),
    ],
    # Claim answer: a claim has no send mode (always false in v14)
    (344, None): [("object.send_mode == &quot;digital&quot;", "False")],
    (377, "it_IT"): [
        (
            '{{"vostro" if plural = object.partner_id.title.plural or '
            'object.partner_id.title.id == 29 else "tuo")}}',
            '{{"vostro" if object.partner_id.title.plural or '
            'object.partner_id.title.id == 29 else "tuo"}}',
        )
    ],
    # The communication is about the partner, not a user
    (453, None): [("user.login", "user.user_ids[:1].login")],
    (458, None): TASK_USER,
    (459, None): TASK_USER,
    (461, None): TASK_USER,
    (514, "it_IT"): [
        (
            re.compile(
                r'(<t t-set="partner" t-value="object.partner_id"/>)'
                r'(?!<t t-set="children")'
            ),
            r'\1<t t-set="children" t-value="partner.sponsorship_ids.filtered('
            r'&#x27;is_active&#x27;).mapped(&#x27;child_id&#x27;)"/>',
        )
    ],
    # The "if" around the jobs link is never closed
    (537, "de_DE"): [
        (
            re.compile(r"(% if 'website_url' in object\.job_id.*\n.*all our jobs.*\n)"),
            r"\1</t>\n",
        )
    ],
}

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
# src="<t t-out="url"></t>": expression in an attribute, written by a previous
# conversion of a tag on several lines
OUT_IN_ATTR_RE = re.compile(
    r'(?<![\w-])(?P<name>[a-zA-Z][\w:-]*)="<t t-out="(?P<expr>[^"]*)"\s*(?:/>|></t>)"'
)
MULTILINE_TAG_WITH_EXPR_RE = re.compile(r"<[a-zA-Z](?=[^<>]*\n)(?=[^<>]*\$\{)[^<>]*>")
ATTR_WITH_EXPR_RE = re.compile(r'(?P<name>[\w:-]+)="(?P<value>[^"]*\$\{[^"]*)"')
# Jinja filters and their Python equivalent ({} is the filtered value, {args}
# the filter arguments)
FILTERS = {
    "safe": "{}",
    "e": "{}",
    "escape": "{}",
    "lower": "str({}).lower()",
    "upper": "str({}).upper()",
    "capitalize": "str({}).capitalize()",
    "title": "str({}).title()",
    "trim": "str({}).strip()",
    "int": "int({})",
    "float": "float({})",
    "string": "str({})",
    "length": "len({})",
    "abs": "abs({})",
    "sum": "sum({})",
    "first": "{}[0]",
    "last": "{}[-1]",
    "join": "({args}).join({})",
    "default": "({} or {args})",
    "d": "({} or {args})",
    "replace": "str({}).replace({args})",
    "format": "({}) % ({args},)",
    "round": "round({}, {args})",
}
FILTER_START_RE = re.compile(r"\|\s*(?P<name>[a-z_]+)\b(?:\s*(?P<call>\())?")
# Variable names QWeb refuses (non-ASCII letters: wünschst)
SET_NAME_RE = re.compile(
    r'(?:t-set="|^[ \t]*%[ \t]*set[ \t]+)(?P<name>[^\W\d][\w]*)', re.M
)
SNIPPET_STRIPTAGS_RE = re.compile(
    r"get_snippet\((?P<args>[^()]*)\)\s*\|\s*striptags(?:\s*\|\s*safe)?"
)
LEFTOVER_RE = re.compile(
    r"(?m)^[ \t]*%[ \t]*(?:set|if|elif|else|endif|for|endfor)\b|\$\{"
)
# QWeb attributes holding a Python expression
QWEB_ATTR_RE = re.compile(
    r'(?P<attr>t-(?:out|esc|raw|value|if|elif|foreach|att-[\w-]+))="(?P<expr>[^"]*)"'
)
QWEB_ATTRF_RE = re.compile(r'(?P<attr>t-attf-[\w-]+)="(?P<expr>[^"]*)"')
INLINE_RE = re.compile(r"\{\{(?P<expr>.*?)\}\}", re.S)
NAMESPACE_SET_RE = re.compile(
    r'<t t-set="(?P<name>\w+)" t-value="namespace\((?P<args>[^"]*)\)"\s*/>'
    r"|^(?P<indent>[ \t]*)%[ \t]*set[ \t]+(?P<jname>\w+)[ \t]*=[ \t]*"
    r"namespace\((?P<jargs>.*)\)[ \t]*$",
    re.M,
)
ITER_RE = re.compile(r"\.iter(items|values|keys)\(\)")
EMAIL_LINK_RE = re.compile(
    r'<t t-out="&#x27;\(&lt;a href=&quot;\{"></t>"(?P<style>[^>]*)>\{\}</a>\)'
    r"'\.format\(donor\.email, donor\.email\) if (?P<cond>.*?) else ''\}"
)
SUBJECT_PARTNER_RE = re.compile(r"(?<![\w.])partner\.")
# datetime.date(2021, 11, 01): leading zero refused by Python 3
LEADING_ZERO_RE = re.compile(r"(?<![\w.])0+(?=[1-9]\b)")


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


def _compiles(expr):
    try:
        compile(expr.strip(), "<expr>", "eval")
        return True
    except SyntaxError:
        return False


def _renamed(expr, lang):
    for regex, new in RENAMES:
        expr = regex.sub(new, expr)
    if lang == "it_IT" and "oggetto" in expr:
        for regex, new in ITALIAN_CODE:
            expr = _outside_strings_sub(regex, new, expr)
    return _outside_strings_sub(JINJA_LITERALS, lambda m: m[1].capitalize(), expr)


def _repair(expr):
    """Make a Python 2 / Jinja expression valid Python 3. Returns the expression
    unchanged when nothing can be done, the render test reports it."""
    expr = re.sub(r"\s*\n\s*", " ", expr).strip()
    expr = ITER_RE.sub(r".\1()", expr)
    for _i in range(5):
        try:
            compile(expr, "<expr>", "eval")
            return expr
        except SyntaxError as error:
            if error.msg == "expected 'else' after 'if' expression":
                # Jinja: no else renders nothing
                pos = error.end_offset - 1
                expr = f"{expr[:pos]} else ''{expr[pos:]}"
            elif error.msg.startswith("leading zeros"):
                expr = _outside_strings_sub(LEADING_ZERO_RE, "", expr)
            else:
                return expr
    return expr


def _outside_strings_sub(regex, repl, text):
    spans = _string_spans(text)

    def sub(match):
        if _span_at(spans, match.start()):
            return match[0]
        return repl(match) if callable(repl) else match.expand(repl)

    return regex.sub(sub, text)


def _string_spans(expr):
    spans, quote, begin = [], None, 0
    for pos, char in enumerate(expr):
        if quote:
            if char == quote and expr[pos - 1] != "\\":
                spans.append((begin, pos))
                quote = None
        elif char in "'\"":
            quote, begin = char, pos
    return spans


def _span_at(spans, pos):
    return next((span for span in spans if span[0] <= pos <= span[1]), None)


def _matching(expr, pos, step, spans):
    """Position of the bracket matching the one at pos (step 1 or -1)"""
    depth = 0
    while 0 <= pos < len(expr):
        span = _span_at(spans, pos)
        if span:
            pos = span[1] + 1 if step > 0 else span[0] - 1
            continue
        if expr[pos] in "([{":
            depth += step
        elif expr[pos] in ")]}":
            depth -= step
        if depth == 0:
            return pos
        pos += step
    raise ConversionError(f"unbalanced brackets in {expr!r}")


def _operand_start(expr, pos, spans):
    """Start of the primary expression (name, call, subscript, literal) that
    ends before pos."""
    pos -= 1
    while pos >= 0 and expr[pos] == " ":
        pos -= 1
    start = pos + 1
    while pos >= 0:
        span = _span_at(spans, pos)
        if span:
            pos = span[0]
        elif expr[pos] in ")]":
            pos = _matching(expr, pos, -1, spans)
        elif expr[pos].isalnum() or expr[pos] == "_":
            while pos > 0 and (expr[pos - 1].isalnum() or expr[pos - 1] == "_"):
                pos -= 1
        else:
            break
        start = pos
        pos -= 1
        if pos >= 0 and expr[pos] == "." or expr[start] in "([":
            pos -= expr[pos] == "." and 1 or 0
            continue
        if pos >= 0 and (expr[pos].isalnum() or expr[pos] in "_)]"):
            # a call or a subscript: name(...) / x[...]
            continue
        break
    if start > len(expr) - 1 or start < 0:
        raise ConversionError(f"no value before the filter in {expr!r}")
    return start


def _convert_filters(expr):
    """Jinja filters (value|name(args)) -> Python, anywhere in the expression"""
    for _i in range(20):
        spans = _string_spans(expr)
        match = next(
            (
                m
                for m in FILTER_START_RE.finditer(expr)
                if not _span_at(spans, m.start())
                and m["name"] in FILTERS
                and expr[m.start() + 1 : m.start() + 2] != "|"
            ),
            None,
        )
        if not match:
            return expr
        start = _operand_start(expr, match.start(), spans)
        end, args = match.end(), ""
        if match["call"]:
            close = _matching(expr, match.end() - 1, 1, spans)
            args, end = expr[match.end() : close], close + 1
        value = expr[start : match.start()].strip()
        python = FILTERS[match["name"]].format(value, args=args or "''")
        expr = f"{expr[:start]}({python}){expr[end:]}"
    raise ConversionError(f"too many filters in {expr!r}")


def _expr(expr, loops=()):
    """Jinja expression -> Python expression (unescaped)."""
    expr = html.unescape(expr).strip()
    expr = SNIPPET_STRIPTAGS_RE.sub(
        lambda m: f"get_snippet({m['args']}, strip_html=True)", expr
    )
    expr = _convert_filters(expr)
    for var in loops:
        expr = re.sub(r"\bloop\.index0\b", f"{var}_index", expr)
        expr = re.sub(r"\bloop\.index\b", f"({var}_index + 1)", expr)
        expr = re.sub(r"\bloop\.first\b", f"{var}_first", expr)
        expr = re.sub(r"\bloop\.last\b", f"{var}_last", expr)
        expr = re.sub(r"\bloop\.length\b", f"{var}_size", expr)
    if "loop." in expr or " is defined" in expr:
        raise ConversionError(f"unsupported Jinja syntax in {expr!r}")
    return _repair(expr)


def _attr(expr):
    return html.escape(expr, quote=True)


def _convert_tag(tag, loops):
    """${expressions} in the attributes of a tag -> t-attf-attribute"""

    def attr_sub(match):
        value = EXPR_RE.sub(
            lambda e: "{{ " + _expr(e["expr"], loops) + " }}",
            html.unescape(match["value"]),
        )
        return f't-attf-{match["name"]}="{_attr(value)}"'

    return ATTR_WITH_EXPR_RE.sub(attr_sub, tag)


def _convert_line(line, loops):
    line = TAG_WITH_EXPR_RE.sub(lambda tag: _convert_tag(tag[0], loops), line)
    return EXPR_RE.sub(lambda e: f'<t t-out="{_attr(_expr(e["expr"], loops))}"/>', line)


def _foreach(indent, rest, loops):
    """% for a in b / % for a, b in c"""
    target, sep, iterable = rest.partition(" in ")
    names = [name.strip() for name in target.split(",")]
    if not sep or not all(name.isidentifier() for name in names):
        raise ConversionError(f"cannot convert for {rest!r}")
    if len(names) == 1:
        loops.append(names[0])
        return (
            f'{indent}<t t-foreach="{_attr(_expr(iterable, loops))}" '
            f't-as="{names[0]}">'
        )
    item = "_".join(names) + "_item"
    loops.append(item)
    unpack = "".join(
        f'<t t-set="{name}" t-value="{item}[{index}]"/>'
        for index, name in enumerate(names)
    )
    return (
        f'{indent}<t t-foreach="{_attr(_expr(iterable, loops))}" t-as="{item}">'
        + unpack
    )


def _convert_body(body):
    """Convert the Jinja line statements and ${expressions} of a body. Works
    for fully Jinja texts as well as for half converted ones, where a stray
    "% endif" closes a <t t-if> written in QWeb."""
    # Tags written on several lines: their attributes are converted first, as
    # the rest of the text is converted line by line
    body = MULTILINE_TAG_WITH_EXPR_RE.sub(lambda tag: _convert_tag(tag[0], ()), body)
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
            out.append(_foreach(indent, rest, loops))
    return "\n".join(out)


def _namespace_args(args):
    call = ast.parse(f"f({html.unescape(args)})", mode="eval").body
    return [(kw.arg, ast.unparse(kw.value)) for kw in call.keywords]


def _remove_namespaces(text):
    """namespace(a=1) only exists in Jinja. QWeb variables set in a loop stay
    set after it, so ns.a becomes a plain variable ns_a."""
    names = []

    def sub(match):
        if match["name"]:
            names.append(match["name"])
            return "".join(
                f'<t t-set="{match["name"]}_{key}" t-value="{_attr(value)}"/>'
                for key, value in _namespace_args(match["args"])
            )
        names.append(match["jname"])
        return "\n".join(
            f"{match['indent']}% set {match['jname']}_{key} = {value}"
            for key, value in _namespace_args(match["jargs"])
        )

    text = NAMESPACE_SET_RE.sub(sub, text)
    for name in names:
        text = re.sub(rf"\b{name}\.(\w+)\b", rf"{name}_\1", text)
    return text


def _fix_qweb_expressions(body, lang):
    """Jinja filters, multi-line expressions, Python 2 code and removed fields
    in the QWeb attributes. Attributes are only rewritten when they change."""

    def fix(expr):
        renamed = _renamed(expr, lang)
        spans = _string_spans(renamed)
        has_filter = SNIPPET_STRIPTAGS_RE.search(renamed) or any(
            not _span_at(spans, m.start()) and m["name"] in FILTERS
            for m in FILTER_START_RE.finditer(renamed)
        )
        if (
            renamed == expr
            and not has_filter
            and not ITER_RE.search(expr)
            and _compiles(expr)
        ):
            return expr
        try:
            return _expr(renamed)
        except ConversionError:
            return _repair(renamed)

    def attr_sub(match):
        expr = html.unescape(match["expr"])
        new = fix(expr)
        if new == expr:
            return match[0]
        return f'{match["attr"]}="{_attr(new)}"'

    def attrf_sub(match):
        value = html.unescape(match["expr"])
        new = INLINE_RE.sub(
            lambda m: m[0]
            if fix(m["expr"]).strip() == m["expr"].strip()
            else "{{ " + fix(m["expr"]) + " }}",
            value,
        )
        if new == value:
            return match[0]
        return f'{match["attr"]}="{_attr(new)}"'

    body = QWEB_ATTR_RE.sub(attr_sub, body)
    return QWEB_ATTRF_RE.sub(attrf_sub, body)


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


class _Subject:
    """Jinja subject (set lines, if blocks, ${} and {{}}) -> inline template.
    Text lines are joined with a space, like the mail client does."""

    def __init__(self, subject):
        self.lines = [line for line in subject.split("\n") if line.strip()]
        self.pos = 0

    def convert(self):
        variables, parts, conditional = self._block({}, ())
        if self.pos < len(self.lines):
            raise ConversionError(f"unexpected {self.lines[self.pos].strip()!r}")
        if not conditional:
            return " ".join(
                INLINE_RE.sub(
                    lambda m: "{{ " + self._inline(m["expr"], variables) + " }}",
                    EXPR_RE.sub(lambda m: "{{" + m["expr"] + "}}", line),
                )
                for line in self.raw_parts
            )
        joined = ", ".join(parts)
        return "{{ ' '.join([part for part in [" + joined + "] if part]) }}"

    def _inline(self, expr, variables):
        expr = _expr(expr)
        for var, value in variables.items():
            expr = re.sub(rf"(?<![\w.]){var}\b", lambda _m, v=value: v, expr)
        return expr

    def _text(self, line, variables):
        pieces = re.split(r"\$\{((?:[^{}]|\{[^{}]*\})*)\}|\{\{(.*?)\}\}", line)
        exprs = []
        for index in range(0, len(pieces), 3):
            if pieces[index]:
                exprs.append(repr(pieces[index]))
            if index + 1 < len(pieces):
                expr = pieces[index + 1] or pieces[index + 2]
                exprs.append(f"str({self._inline(expr, variables)})")
        return " + ".join(exprs) or "''"

    def _block(self, variables, stops):
        """Read lines until one of the stop keywords. Returns the variables,
        the text parts (Python expressions) and whether an if block holds text."""
        variables, parts, conditional = dict(variables), [], False
        self.raw_parts = []
        while self.pos < len(self.lines):
            line = self.lines[self.pos]
            match = STATEMENT_RE.match(line)
            if match and match["kw"] in stops:
                break
            self.pos += 1
            if not match:
                parts.append(self._text(line.strip(), variables))
                self.raw_parts.append(line.strip())
                continue
            kw, rest = match["kw"], match["rest"].strip().rstrip(":").strip()
            if kw == "set":
                name, sep, value = rest.partition("=")
                if not sep or not name.strip().isidentifier():
                    raise ConversionError(f"cannot convert {line.strip()!r}")
                variables[name.strip()] = f"({self._inline(value, variables)})"
            elif kw == "if":
                branches = []
                cond = self._inline(rest, variables)
                while True:
                    raw_parts = self.raw_parts
                    b_vars, b_parts, _cond = self._block(
                        variables, ("elif", "else", "endif")
                    )
                    self.raw_parts = raw_parts
                    branches.append((cond, b_vars, b_parts))
                    if self.pos >= len(self.lines):
                        raise ConversionError("% if without % endif in subject")
                    end = STATEMENT_RE.match(self.lines[self.pos])
                    self.pos += 1
                    end_rest = end["rest"].strip().rstrip(":").strip()
                    if end["kw"] == "endif":
                        break
                    cond = (
                        self._inline(end_rest, variables)
                        if end["kw"] == "elif"
                        else None
                    )
                for var in {var for _c, b_vars, _p in branches for var in b_vars}:
                    value = variables.get(var, "None")
                    for b_cond, b_vars, _p in reversed(branches):
                        b_value = b_vars.get(var, variables.get(var, "None"))
                        if b_vars.get(var) == variables.get(var):
                            continue
                        value = (
                            b_value
                            if b_cond is None
                            else f"({b_value} if {b_cond} else {value})"
                        )
                    variables[var] = value
                if any(b_parts for _c, _v, b_parts in branches):
                    conditional = True
                    value = "''"
                    for b_cond, _v, b_parts in reversed(branches):
                        text = " + ' ' + ".join(b_parts) or "''"
                        value = (
                            f"({text})"
                            if b_cond is None
                            else f"(({text}) if {b_cond} else {value})"
                        )
                    parts.append(value)
            else:
                raise ConversionError(f"unexpected {line.strip()!r} in subject")
        return variables, parts, conditional


def _ascii_names(body):
    """QWeb variable names must be ASCII: wünschst -> wunschst. Only the names
    are renamed, in the t-set and in the expressions, not the text."""
    names = {name for name in SET_NAME_RE.findall(body) if not name.isascii()}
    if not names:
        return body
    renames = {
        name: unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
        for name in names
    }
    name_re = re.compile(
        r"(?<![\w.])(" + "|".join(map(re.escape, renames)) + r")(?!\w)"
    )

    def rename(text):
        return _outside_strings_sub(name_re, lambda m: renames[m[1]], text)

    body = re.sub(
        r'(t-set=")([^"]+)(")', lambda m: m[1] + renames.get(m[2], m[2]) + m[3], body
    )

    def attr_sub(match):
        expr = html.unescape(match["expr"])
        new = rename(expr)
        return match[0] if new == expr else f'{match["attr"]}="{_attr(new)}"'

    body = QWEB_ATTR_RE.sub(attr_sub, body)
    return QWEB_ATTRF_RE.sub(
        lambda m: f'{m["attr"]}="'
        + _attr(
            INLINE_RE.sub(
                lambda i: "{{" + rename(i["expr"]) + "}}", html.unescape(m["expr"])
            )
        )
        + '"'
        if INLINE_RE.search(m["expr"]) and name_re.search(m["expr"])
        else m[0],
        body,
    )


def _fix_loops(body):
    """loop.index of Jinja in QWeb loops: <t t-foreach="..." t-as="i"> gives
    i_index, i_first, i_last, i_size."""

    def attr_sub(match, loop_var):
        expr = html.unescape(match["expr"])
        new = LOOP_RE.sub(lambda m: LOOP_VARS[m[1]].format(loop_var), expr)
        return match[0] if new == expr else f'{match["attr"]}="{_attr(new)}"'

    out, pos = [], 0
    for match in QWEB_ATTR_RE.finditer(body):
        if not LOOP_RE.search(html.unescape(match["expr"])):
            continue
        loop_vars = re.findall(r't-as="(\w+)"', body[: match.start()])
        if not loop_vars:
            continue
        out += [body[pos : match.start()], attr_sub(match, loop_vars[-1])]
        pos = match.end()
    return "".join(out) + body[pos:]


def _fix_email_links(body):
    """${'(<a href="{}">{}</a>)'.format(email, email) if ... else ''} cut in
    two at the first } by the migration"""

    def sub(match):
        return (
            f'<t t-if="{_attr(html.unescape(match["cond"]))}">(<a '
            f't-att-href="&#x27;mailto:&#x27; + donor.email"{match["style"]}>'
            '<t t-out="donor.email"/></a>)</t>'
        )

    return EMAIL_LINK_RE.sub(sub, body)


def _is_broken(text):
    if LEFTOVER_RE.search(text):
        return True
    return any(
        not _compiles(html.unescape(match["expr"]))
        for match in QWEB_ATTR_RE.finditer(text)
    )


def _fix_body(body, template_id, lang):
    if not body or not body.strip():
        return body
    original = body
    body = _apply_specific(body, template_id, lang)
    body = _fix_email_links(body)
    body = _remove_namespaces(body)
    if LEFTOVER_RE.search(body):
        body = _convert_body(body)
    body = OUT_IN_ATTR_RE.sub(r't-attf-\g<name>="{{ \g<expr> }}"', body)
    body = _ascii_names(body)
    body = _fix_loops(body)
    body = _fix_qweb_expressions(body, lang)
    _check_blocks(original, body)
    return body


def _fix_subject(subject, template_id, lang):
    if not subject:
        return subject
    subject = _apply_specific(subject, template_id, lang)
    if LEFTOVER_RE.search(subject):
        subject = _Subject(subject).convert()

    def fix(match):
        expr = _renamed(match["expr"], lang)
        # variables of the body are not set in the subject
        expr = SUBJECT_PARTNER_RE.sub("object.partner_id.", expr)
        if expr == match["expr"] and _compiles(expr):
            return match[0]
        return "{{ " + _repair(expr) + " }}"

    return INLINE_RE.sub(fix, subject)


def _fix_char(value, template_id, lang):
    """email_to, partner_to...: ${expr} -> {{ expr }}"""
    if not value or "${" not in value:
        return value

    def sub(match):
        expr = _expr(match["expr"])
        # ${object.user_id|safe} printed the user record, not its address
        if expr.strip("() ") == "object.user_id":
            expr = "object.user_id.email"
        return "{{ " + expr + " }}"

    return EXPR_RE.sub(sub, value)


def _apply_specific(text, template_id, lang):
    for key in ((template_id, None), (template_id, lang)):
        for old, new in SPECIFIC.get(key, []):
            text = old.sub(new, text) if hasattr(old, "sub") else text.replace(old, new)
    return text


def _fix_translated(env, template, field, fixer):
    env.cr.execute(f"SELECT {field} FROM mail_template WHERE id = %s", (template[0],))
    values = env.cr.fetchone()[0] or {}
    fixed, changed = dict(values), []
    for lang in LANGS:
        value = values.get(lang)
        if not value:
            continue
        restored = RESTORED.get((template[0], lang))
        if field == "body_html" and restored == template[1] and _is_broken(value):
            path = os.path.join(RESTORED_DIR, f"{template[0]}_{lang}.jinja")
            with open(path, encoding="utf-8") as text:
                value = text.read()
        try:
            fixed[lang] = fixer(value, template[0], lang)
        except (ConversionError, SyntaxError) as error:
            _logger.warning(
                "%s (mail.template %s, %s %s) could not be converted, please "
                "check it: %s",
                template[1],
                template[0],
                field,
                lang,
                error,
            )
            fixed[lang] = value
        if fixed[lang] != values.get(lang):
            changed.append(lang)
    if changed:
        env.cr.execute(
            f"UPDATE mail_template SET {field} = %s WHERE id = %s",
            (json.dumps(fixed), template[0]),
        )
    return changed


def _check_specific_names(env):
    """The fixes by id only apply to the expected templates"""
    for template_id, name in SPECIFIC_NAMES.items():
        env.cr.execute(
            "SELECT name->>'en_US' FROM mail_template WHERE id = %s", (template_id,)
        )
        row = env.cr.fetchone()
        if not row or row[0] != name:
            _logger.warning(
                "mail.template %s is not %r, its specific fixes are skipped",
                template_id,
                name,
            )
            for key in [key for key in SPECIFIC if key[0] == template_id]:
                del SPECIFIC[key]


def fix_templates(env):
    _check_specific_names(env)
    env.cr.execute("SELECT id, name->>'en_US' FROM mail_template ORDER BY id")
    for template in env.cr.fetchall():
        changes = {
            "subject": _fix_translated(env, template, "subject", _fix_subject),
            "body": _fix_translated(env, template, "body_html", _fix_body),
        }
        for field in ("email_to", "email_cc", "partner_to", "reply_to"):
            env.cr.execute(
                f"SELECT {field} FROM mail_template WHERE id = %s", (template[0],)
            )
            value = env.cr.fetchone()[0]
            new = _fix_char(value, template[0], None)
            if new != value:
                env.cr.execute(
                    f"UPDATE mail_template SET {field} = %s WHERE id = %s",
                    (new, template[0]),
                )
                changes[field] = ["all"]
        changes = {field: langs for field, langs in changes.items() if langs}
        if changes:
            _logger.info(
                "%s (mail.template %s): fixed %s",
                template[1],
                template[0],
                ", ".join(f"{f} {' '.join(langs)}" for f, langs in changes.items()),
            )
    env["mail.template"].invalidate_model()


def archive_templates(env):
    for template_id, name in ARCHIVED.items():
        env.cr.execute(
            """
            UPDATE mail_template t SET active = FALSE
            WHERE id = %s AND name->>'en_US' = %s AND active
            AND NOT EXISTS (
                SELECT 1 FROM partner_communication_config c
                WHERE c.email_template_id = t.id AND c.active
            )
            """,
            (template_id, name),
        )
        if env.cr.rowcount:
            _logger.info("Archived mail.template %s %s", template_id, name)


def reset_templates(env):
    for xmlid, v14_code in RESET.items():
        template = env.ref(xmlid, raise_if_not_found=False)
        if not template:
            continue
        env.cr.execute(
            "SELECT body_html FROM mail_template WHERE id = %s", (template.id,)
        )
        bodies = env.cr.fetchone()[0] or {}
        if any(v14_code.search(bodies.get(lang) or "") for lang in LANGS):
            template.reset_template()
            _logger.info("Reloaded mail.template %s from its module", xmlid)


def run(env):
    archive_templates(env)
    reset_templates(env)
    fix_templates(env)


@openupgrade.migrate()
def migrate(env, version):
    run(env)
