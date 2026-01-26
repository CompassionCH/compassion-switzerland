import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    # -------------------------------------------------------------------------
    # Remove 'calendar' field from views to prevent Validation Error
    # -------------------------------------------------------------------------
    # The 'calendar' field was removed from the python model, but old views in
    # the database still reference it. We must remove these references before Odoo tries
    # to load the registry, or the update will crash.
    _logger.info("Removing 'calendar' field references from res.partner views...")

    env.cr.execute(
        """
                   UPDATE ir_ui_view
                   SET arch_db = regexp_replace(
                           arch_db,
                           '<field name="calendar"[^>]*/>', '', 'g'
                   )
                   WHERE model = 'res.partner' AND arch_db LIKE '%name="calendar"%';
                   """
    )
