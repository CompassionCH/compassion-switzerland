from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return
    openupgrade.load_xml(env.cr, "partner_communication_switzerland", "data/translator_action_rules.xml")
