from openupgradelib import openupgrade


def migrate(cr, installed_version):
    if not installed_version:
        return

    # Copy start_date over onboarding_start_date
    cr.execute(
        """
        UPDATE recurring_contract
        SET onboarding_start_date = start_date
        WHERE is_first_sponsorship = true
    """
    )
    # Update data
    openupgrade.load_xml(
        cr, "partner_communication_switzerland", "data/onboarding_process.xml"
    )
