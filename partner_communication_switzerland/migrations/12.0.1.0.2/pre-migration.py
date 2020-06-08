from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(cr, version):
    if not version:
        return
    openupgrade.load_xml(cr, "partner_communication_switzerland", "data/translator_action_rules.xml")
