from openupgradelib import openupgrade


def migrate(cr, installed_version):
    if not installed_version:
        return

    # Update data
    openupgrade.load_xml(
        cr, "partner_communication_switzerland", "data/onboarding_process.xml")
