from openupgradelib import openupgrade


def migrate(cr, version):
    if not version:
        return

    # Force loading products configuration
    openupgrade.load_xml(cr, "crowdfunding_compassion", "data/products.xml")
