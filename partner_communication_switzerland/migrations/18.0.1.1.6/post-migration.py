import logging
import os

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

# These translations only exist in the database. They were never converted
# from the v14 Jinja syntax ("% set", "${...}") to QWeb, and read the v14
# survey.public_url field, which no longer exists: they either can't be
# rendered or show raw Jinja code and a dead survey link. The converted texts
# are stored next to this script as <template xmlid>.<lang>.html.
CONVERTED_TEMPLATES = {
    "mail_onboarding_step5": ("de_DE", "it_IT"),
    "wrpr_upgrade_confirmation": ("fr_CH", "de_DE", "it_IT"),
}


@openupgrade.migrate()
def migrate(env, version):
    # The French and Italian Write&Pray welcome only read the removed
    # survey.public_url field, which prevents the welcome from being created.
    template = env.ref("partner_communication_switzerland.mail_wrpr_welcome")
    for lang in ("fr_CH", "it_IT"):
        t_template = template.with_context(lang=lang)
        body = t_template.body_html or ""
        if ").public_url" in body:
            t_template.body_html = body.replace(").public_url", ").get_start_url()")
            _logger.info("Fixed the survey link of the %s Write&Pray welcome", lang)

    folder = os.path.dirname(__file__)
    for xmlid, langs in CONVERTED_TEMPLATES.items():
        template = env.ref(f"partner_communication_switzerland.{xmlid}")
        for lang in langs:
            with open(os.path.join(folder, f"{xmlid}.{lang}.html")) as body:
                template.with_context(lang=lang).body_html = body.read()
            _logger.info("Converted the %s text of %s to QWeb", lang, template.name)
