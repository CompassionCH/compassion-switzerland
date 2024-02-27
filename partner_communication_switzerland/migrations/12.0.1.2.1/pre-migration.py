from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, installed_version):
    if not installed_version:
        return

    csp_1 = env["partner.communication.config"].search([("name", "ilike", "CSP 1")])
    openupgrade.add_xmlid(
        env.cr,
        "partner_communication_switzerland",
        "csp_1",
        "partner.communication.config",
        csp_1.id,
    )
