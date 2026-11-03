import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    """Partners created in v14 (mostly 2017-2018) have no address type. Since
    18.0 the partner form requires it for individuals, so saving the form, which
    every smart button does first, fails with "Invalid fields: Address Type"
    (T3618). Give them the default type, as for any new contact.
    """
    env.cr.execute("UPDATE res_partner SET type = 'contact' WHERE type IS NULL")
    _logger.info("T3618: address type set to 'contact' on %s partners", env.cr.rowcount)
