from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return

    # Force update mail template notification
    openupgrade.set_xml_ids_noupdate_value(
        env, "muskathlon", ["order_material_mail_template"], False)
