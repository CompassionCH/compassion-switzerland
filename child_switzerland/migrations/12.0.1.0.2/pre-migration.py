from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return

    # FIX xml_id for child_his_en
    openupgrade.add_xmlid(env.cr, "child_switzerland", "child_his_en", "ir.advanced.translation", 442)
