from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, installed_version):
    if not installed_version:
        return

    csp_2a = env["partner.communication.config"].search([("name", "ilike", "CSP 2a")])
    openupgrade.add_xmlid(
        env.cr,
        "partner_communication_switzerland",
        "csp_2a",
        "partner.communication.config",
        csp_2a.id,
    )
