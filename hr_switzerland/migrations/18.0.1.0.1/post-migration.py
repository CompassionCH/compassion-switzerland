import json
import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

# T3520: the department name is shown in the signature of printed
# communications. Its translations were lost in the migration from v14 (the
# field is only translatable because of this module), so letters showed the
# English name in every language. These are the translations from v14, found by
# the English name. Languages already translated in the database are kept.
TRANSLATIONS = {
    "Opérations": {"de_DE": "Operations", "it_IT": "Operations"},
    "Sponsor and Donor Services": {
        "de_DE": "Patenschaften",
        "fr_CH": "Département Parrainage",
        "it_IT": "Dipartimento di Sostegno",
    },
    "CEO": {"de_DE": "Geschäftsleiter", "fr_CH": "Directeur"},
    "Donors relation": {
        "de_DE": "Spenderbetreuung",
        "fr_CH": "Relation donateurs",
        "it_IT": "Relazioni donatori",
    },
    "Church Engagement": {
        "de_DE": "Kontakt Kirchen und Gemeinden",
        "fr_CH": "Contact avec les églises et communautés",
    },
    "Events": {
        "de_DE": "Events & Community Engagement",
        "fr_CH": "Events & Community Engagement",
        "it_IT": "Events & Community Engagement",
    },
}


@openupgrade.migrate()
def migrate(env, version):
    # SQL rather than a translated write, which would also overwrite the
    # stored complete_name with the translated value.
    for name, translations in TRANSLATIONS.items():
        env.cr.execute(
            """
            UPDATE hr_department
            SET name = %s::jsonb || name
            WHERE name->>'en_US' = %s
            """,
            (json.dumps(translations), name),
        )
        _logger.info("Department %s: %s translated", name, env.cr.rowcount)
    env["hr.department"].invalidate_model(["name"])
