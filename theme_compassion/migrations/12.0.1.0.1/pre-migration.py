from openupgradelib import openupgrade


def migrate(cr, version):
    if not version:
        return

    # Force reload security rules that have changed
    openupgrade.rename_xmlids(cr, [
        ("theme_compassion.layout", "website_compassion.layout")
    ])
