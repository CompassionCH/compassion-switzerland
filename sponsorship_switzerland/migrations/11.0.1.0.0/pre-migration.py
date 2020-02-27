from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return

    openupgrade.set_xml_ids_noupdate_value(
        env, 'sponsorship_switzerland', ['journal_raif', 'journal_post'], False)
