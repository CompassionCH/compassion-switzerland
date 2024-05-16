from openupgradelib import openupgrade


def migrate(cr, installed_version):
    if not installed_version:
        return
    openupgrade.load_xml(cr, "sbc_switzerland", "data/translator_action_rules.xml")
