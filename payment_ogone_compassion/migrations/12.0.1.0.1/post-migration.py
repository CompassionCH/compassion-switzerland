from openupgradelib import openupgrade


def migrate(cr, version):
    if not version:
        return

    openupgrade.load_xml(
        cr, "payment_ogone_compassion", "data/payment_icon.xml")
