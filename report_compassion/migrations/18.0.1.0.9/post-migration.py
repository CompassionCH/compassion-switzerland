import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    """The signature picture lost its round shape (border-radius) in the
    18.0 migration (T3613). signatures.xml is noupdate, so upgrading the module
    never reloads the template: reset it to the file version.
    """
    view = env.ref("report_compassion.user_signature", raise_if_not_found=False)
    if view and "border-radius: 50%" not in (
        view.with_context(lang=None).arch_db or ""
    ):
        view.reset_arch(mode="hard")
        _logger.info("T3613: reset report_compassion.user_signature arch")
