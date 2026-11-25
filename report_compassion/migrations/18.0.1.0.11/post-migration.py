import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    """T3484: signatures.xml is noupdate; reload it for the explicit image sizes."""
    view = env.ref("report_compassion.user_signature", raise_if_not_found=False)
    if view and "height: 26px" not in (view.with_context(lang=None).arch_db or ""):
        view.reset_arch(mode="hard")
        _logger.info("T3484: reset report_compassion.user_signature arch")
