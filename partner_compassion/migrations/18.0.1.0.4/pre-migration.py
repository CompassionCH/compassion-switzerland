import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    """T3642 The "Email alias" partner type is removed, the standard "Other
    Address" type is used for the aliases of a contact. Must run before the
    selection value is removed, which would reset the type to the default.
    """
    env.cr.execute(
        """
        UPDATE res_partner
        SET type = CASE WHEN parent_id IS NULL THEN 'contact' ELSE 'other' END
        WHERE type = 'email_alias'
        """
    )
    _logger.info("T3642: type email_alias replaced on %s partners", env.cr.rowcount)
