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
    Pre-migration script to standardize 'advocate.engagement' records.

    1. Fix XML IDs:
       - Assigns a proper XML ID ('partner_compassion.engagement_together') to the
         'Together' record (ID 24) which was missing one.
       - Renames the auto-generated '__export__' ID of 'Prayer' (ID 19) to
         'partner_compassion.engagement_pray'.
       Goal: Link existing production records to the new XML data files to prevent
             duplicates during the module update.

    2. Refresh Translations:
       - Deletes old translations for MyCompassion fields (label, alt_text, description)
         on target records.
       - Goal: Force Odoo to reload the latest translations from the module's .po files.
    """
    cr = env.cr

    # -------------------------------------------------------------------------
    # XML_IDS MANAGEMENT
    # -------------------------------------------------------------------------

    # Add missing XML_ID for Together engagement type
    openupgrade.add_xmlid(
        cr,
        "partner_compassion",
        "engagement_together",
        "advocate.engagement",
        ENGAGEMENT_TYPE_ID_TOGETHER,
        noupdate=False,
    )

    # Rename old "__export__" IDs to proper module IDs
    cr.execute(
        "SELECT module, name FROM ir_model_data WHERE model = %s AND res_id = %s",
        ("advocate.engagement", ENGAGEMENT_TYPE_ID_PRAYER),
    )
    res = cr.fetchone()

    if res:
        old_module, old_name = res
        openupgrade.rename_xmlids(
            cr,
            [(f"{old_module}.{old_name}", "partner_compassion.engagement_pray")],
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
