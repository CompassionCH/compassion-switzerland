from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, installed_version):
    if not installed_version:
        return

    churches = env["res.partner"].search([("is_church", "=", True)])
    churches.update_number_sponsorships()
