from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return

    # Allow updating languages
    openupgrade.set_xml_ids_noupdate_value(
        env, "child_switzerland", [
            "lang_compassion_german", "lang_compassion_italian"
        ], False)
