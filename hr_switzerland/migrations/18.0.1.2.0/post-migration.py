import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    # Private partner of the employees: former address_home_id (column kept
    # since the migration to 18.0, field removed in 17.0).
    if not openupgrade.column_exists(env.cr, "hr_employee", "address_home_id"):
        return
    env.cr.execute(
        """
        UPDATE hr_employee e SET private_partner_id = e.address_home_id
          FROM res_partner p
         WHERE p.id = e.address_home_id
           AND e.private_partner_id IS NULL
           AND NOT COALESCE(p.is_company, FALSE)
        """
    )
    _logger.info("Private partner set on %s employees", env.cr.rowcount)
