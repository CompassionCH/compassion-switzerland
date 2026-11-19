from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.set_xml_ids_noupdate_value(
        env,
        "report_compassion",
        ["communication_style", "style", "anniversary_card"],
        False,
    )
    openupgrade.delete_records_safely_by_xml_id(
        env, ["report_compassion.report_compassion_qr_parent"], True
    )
