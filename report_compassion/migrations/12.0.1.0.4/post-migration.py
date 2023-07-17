from openupgradelib import openupgrade


def migrate(cr, version):
    if not version:
        return

    # Force loading new childpack reports
    openupgrade.load_xml(cr, "report_compassion", "report/childpack.xml")
