import base64
import json
import logging
import os

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

# Church presentation texts (en_US, fr_CH, de_DE, it_IT) and photo of the project
# director of a few Frontline Church Partners, matched on the FCP id and loaded on
# the "Donor-funded FCP" intervention of the center (only one must exist).
# The photos are not published on GitHub: they are loaded only if they are copied
# in the director_photos folder (<FCP id>.jpg) before the upgrade, otherwise they
# are skipped. They were resized (600x800 max) and compressed to be used in e-mails.
HERE = os.path.dirname(os.path.abspath(__file__))
PHOTOS = os.path.join(HERE, "director_photos")
TEXT_LANGS = ("fr_CH", "de_DE", "it_IT")


def _set_texts(intervention, texts, installed):
    """The text is translated by terms (paragraphs): the English one is the source
    and the others are linked to it, the texts having the same structure."""
    field = intervention._fields["church_presentation_text"]
    intervention.with_context(lang="en_US").church_presentation_text = texts["en_US"]
    for lang in TEXT_LANGS:
        if lang not in installed:
            continue
        terms = field.get_translation_dictionary(texts["en_US"], {lang: texts[lang]})
        intervention.update_field_translations(
            "church_presentation_text",
            {lang: {term: value[lang] for term, value in terms.items() if value}},
        )


def _load_presentations(env):
    with open(os.path.join(HERE, "church_presentations.json"), encoding="utf-8") as f:
        presentations = json.load(f)
    installed = {code for code, _name in env["res.lang"].get_installed()}
    for fcp_id, texts in presentations.items():
        project = env["compassion.project"].search([("fcp_id", "=", fcp_id)])
        if not project:
            _logger.warning("Church presentation: project %s not found", fcp_id)
            continue
        interventions = project.intervention_ids.filtered(
            lambda i: i.type == "Donor-funded FCP"
        )
        if len(interventions) != 1:
            _logger.warning(
                "Church presentation: %s Donor-funded FCP interventions for %s, "
                "exactly one is expected: skipped",
                len(interventions),
                fcp_id,
            )
            continue
        photo_path = os.path.join(PHOTOS, f"{fcp_id}.jpg")
        photo = False
        if os.path.exists(photo_path):
            with open(photo_path, "rb") as photo_file:
                photo = base64.b64encode(photo_file.read())
        else:
            _logger.info("Church presentation: no photo found for %s", fcp_id)
        if not interventions.church_presentation_text:
            _set_texts(interventions, texts, installed)
        if photo and not interventions.project_director_photo:
            interventions.project_director_photo = photo
        _logger.info(
            "Church presentation loaded for %s (intervention %s)",
            fcp_id,
            interventions.id,
        )


@openupgrade.migrate()
def migrate(env, version):
    _load_presentations(env)
