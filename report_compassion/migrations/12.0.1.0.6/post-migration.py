from openupgradelib import openupgrade


def migrate(cr, version):
    if not version:
        return

    # Force loading new reports
    openupgrade.load_xml(cr, "report_compassion", "report/partner_communication.xml")
