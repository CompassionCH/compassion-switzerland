from openupgradelib import openupgrade


def migrate(cr, installed_version):
    if not installed_version:
        return
    openupgrade.load_xml(cr, 'website_event_compassion',
                         'data/action_rule_past_event.xml')
