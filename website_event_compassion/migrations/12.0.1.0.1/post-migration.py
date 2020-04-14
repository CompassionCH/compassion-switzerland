from openupgradelib import openupgrade


def migrate(cr, version):
    if not version:
        return

    # Force reload security rules that have changed
    openupgrade.load_data(cr, 'website_event_compassion', 'security/access_rules.xml')
