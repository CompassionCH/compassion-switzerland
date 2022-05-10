from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, installed_version):
    if not installed_version:
        return

    openupgrade.set_xml_ids_noupdate_value(env, "partner_communication_switzerland", [
        "sponsorship_anniversary_1_communication",
        "sponsorship_anniversary_3_communication",
        "sponsorship_anniversary_5_communication",
        "sponsorship_anniversary_10_communication",
        "sponsorship_anniversary_15_communication",
    ], False)
    env.cr.execute("""
        DELETE FROM ir_ui_view WHERE arch_db LIKE '%christmas_card%' AND model='res.partner'
        OR inherit_id = ANY (
        SELECT id
        FROM ir_ui_view WHERE arch_db LIKE '%christmas_card%' AND model='res.partner'
        );
        DELETE FROM ir_ui_view WHERE arch_db LIKE '%send_original%' AND model='res.partner'
        OR inherit_id = ANY (
        SELECT id
        FROM ir_ui_view WHERE arch_db LIKE '%send_original%' AND model='res.partner'
        );
    """)
