from openupgradelib import openupgrade

# Specefic Engagement Type IDs (Production Database)
ENGAGEMENT_TYPE_ID_CHURCH = 1
ENGAGEMENT_TYPE_ID_EVENTS = 3
ENGAGEMENT_TYPE_ID_SPORT = 4
ENGAGEMENT_TYPE_ID_PRAYER = 19
ENGAGEMENT_TYPE_ID_TRANSLATION = 21
ENGAGEMENT_TYPE_ID_TOGETHER = 24

# Full list of engagement type targeted by the migration
TARGET_ENGAGEMENT_TYPE_IDS = (
    ENGAGEMENT_TYPE_ID_CHURCH,
    ENGAGEMENT_TYPE_ID_EVENTS,
    ENGAGEMENT_TYPE_ID_SPORT,
    ENGAGEMENT_TYPE_ID_PRAYER,
    ENGAGEMENT_TYPE_ID_TRANSLATION,
    ENGAGEMENT_TYPE_ID_TOGETHER,
)


@openupgrade.migrate()
def migrate(env, version):
    """
    TODO
    """
    cr = env.cr

    # -------------------------------------------------------------------------
    # XML_IDS MANAGEMENT
    # -------------------------------------------------------------------------

    # Add missing XML_ID for Together engagement type
    openupgrade.add_xmlid(
        cr,
        "my_compassion_switzerland",
        "partner_compassion.engagement_together",
        "advocate.engagement",
        ENGAGEMENT_TYPE_ID_TOGETHER,
        noupdate=False,
    )

    # Rename old "__export__" IDs to proper module IDs
    xml_id_mapping = {
        ENGAGEMENT_TYPE_ID_PRAYER: "partner_compassion_engagement_pray",
    }

    for res_id, new_name in xml_id_mapping.items():
        cr.execute(
            "SELECT module, name FROM ir_model_data WHERE model = %s AND res_id = %s",
            ("advocate.engagement", res_id),
        )
        res = cr.fetchone()

        if res:
            old_module, old_name = res
            openupgrade.rename_xmlids(
                cr,
                [(f"{old_module}.{old_name}", f"my_compassion_switzerland.{new_name}")],
            )

        # -------------------------------------------------------------------------
        # CLEANUP OLD TRANSLATIONS
        # -------------------------------------------------------------------------

        # Force Odoo to reload translations from .po file by removing existing ones
        # for the targeted products only.
        cr.execute(
            """
            DELETE FROM ir_translation
            WHERE name IN ('advocate.engagement,my_compassion_alt_text',
                           'advocate.engagement,my_compassion_label',
                           'advocate.engagement,my_compassion_description')
            AND res_id IN %s
            """,
            (TARGET_ENGAGEMENT_TYPE_IDS,),
        )
