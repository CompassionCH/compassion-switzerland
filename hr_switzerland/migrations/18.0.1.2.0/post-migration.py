import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    _set_private_partners(env)
    # Time off on Extra Hours lowers the Odoo extra hours balance: count it in
    # the theoretical time report too (otherwise the day shows 0 theoretical).
    extra_hours = env.ref(
        "hr_holidays_attendance.holiday_status_extra_hours", raise_if_not_found=False
    )
    if extra_hours and not extra_hours.include_in_theoretical:
        extra_hours.include_in_theoretical = True
        _logger.info("Extra Hours: included in theoretical hours")


def _set_private_partners(env):
    # Private partner of the employees: former address_home_id (column kept
    # since the migration to 18.0, field removed in 17.0). Same rule as the
    # domain of the field: a person without parent company.
    if not openupgrade.column_exists(env.cr, "hr_employee", "address_home_id"):
        return
    env.cr.execute(
        """
        UPDATE hr_employee e SET private_partner_id = e.address_home_id
          FROM res_partner p
         WHERE p.id = e.address_home_id
           AND e.private_partner_id IS NULL
           AND NOT COALESCE(p.is_company, FALSE)
           AND p.parent_id IS NULL
        """
    )
    _logger.info("Private partner set on %s employees", env.cr.rowcount)
    env.cr.execute(
        """
        SELECT e.id, e.name, e.address_home_id
          FROM hr_employee e
         WHERE e.active AND e.private_partner_id IS NULL
         ORDER BY e.name
        """
    )
    for emp_id, name, home_id in env.cr.fetchall():
        _logger.warning(
            "Active employee %s %s without private partner (former home partner: %s)",
            emp_id,
            name,
            home_id or "none",
        )
