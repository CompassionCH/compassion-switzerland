from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return

    # Force loading new reports
    openupgrade.set_xml_ids_noupdate_value(env, "report_compassion", [
        "childpack_document", "childpack_small", "childpack_full", "childpack_mini"
    ], False)
