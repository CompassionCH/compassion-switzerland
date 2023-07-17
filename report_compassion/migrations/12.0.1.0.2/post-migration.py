from openupgradelib import openupgrade


def migrate(cr, version):
    if not version:
        return

    # Force loading new BVR reports
    openupgrade.load_xml(cr, "report_compassion", "report/bvr_gift.xml")
    openupgrade.load_xml(cr, "report_compassion", "report/bvr_layout.xml")
    openupgrade.load_xml(cr, "report_compassion", "report/bvr_sponsorship.xml")
