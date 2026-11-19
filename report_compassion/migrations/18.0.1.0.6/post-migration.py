import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

# (lang, male_singular, male_plural) - only German actually distinguishes
# singular/plural for this phrase; French/Italian use the same text either
# way, kept here rather than relying on ir.advanced.translation.get()'s
# _(src) fallback, which can't reach model_terms:ir.ui.view translations
# (those live only in the view's arch_db JSONB, never in ir_translation).
ROWS = [
    ("de_DE", "Deine Spenden im Jahr", "Eure Spenden im Jahr"),
    ("fr_CH", "Vos dons en", "Vos dons en"),
    ("it_IT", "Le Sue donazioni nel", "Le Sue donazioni nel"),
]


@openupgrade.migrate()
def migrate(env, version):
    for lang, male_singular, male_plural in ROWS:
        existing = env["ir.advanced.translation"].search(
            [("src", "=", "Your donations in"), ("lang", "=", lang)]
        )
        if existing:
            _logger.info(
                "T3441: ir.advanced.translation row for 'Your donations in' "
                "(%s) already exists, leaving it untouched.",
                lang,
            )
            continue
        env["ir.advanced.translation"].create(
            {
                "src": "Your donations in",
                "lang": lang,
                "male_singular": male_singular,
                "male_plural": male_plural,
            }
        )
