from openupgradelib import openupgrade


def migrate(cr, version):
    if not version:
        return

    # Force reload security rules that have changed
    openupgrade.load_data(cr, 'muskathlon', 'security/access_rules.xml')
