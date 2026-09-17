import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    """Seed the new configurable official_signer_id, replacing the value
    that used to be hardcoded in the tax_receipt report template
    (partner.env['hr.employee'].browse(44)) - stale, points at a previous
    CEO. Look up the current signer by name rather than carrying the old
    numeric id forward, since that id was exactly the problem.
    """
    employee = env["hr.employee"].search([("name", "=", "Philippe Genre")], limit=1)
    if not employee:
        _logger.warning(
            "T3441: could not find employee 'Philippe Genre' to seed "
            "res.company.official_signer_id - leaving it unset, configure "
            "manually via Settings > Companies > Official Documents."
        )
        return
    env["res.company"].search([]).write({"official_signer_id": employee.id})
