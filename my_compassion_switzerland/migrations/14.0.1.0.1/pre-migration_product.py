from openupgradelib import openupgrade

# -------------------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------------------

# Specific Product IDs (Production Database)
PRODUCT_ID_SURVIVAL = 15
PRODUCT_ID_CHRISTMAS = 31
PRODUCT_ID_UNSPONSORED_CHILD = 39
PRODUCT_ID_WASH = 41
PRODUCT_ID_DISASTER = 238
PRODUCT_ID_FOOD = 303
PRODUCT_ID_HEALTH = 474

# Specific Default code
PRODUCT_DEFAULT_CODE_SURVIVAL = "survival_survie"
PRODUCT_DEFAULT_CODE_CHRISTMAS = "noel"
PRODUCT_DEFAULT_CODE_UNSPONSORED_CHILD = "sansparrain"
PRODUCT_DEFAULT_CODE_WASH = "wash"
PRODUCT_DEFAULT_CODE_DISASTER = "drf_ET"
PRODUCT_DEFAULT_CODE_FOOD = "drf_food-business"
PRODUCT_DEFAULT_CODE_HEALTH = "health_TG"

# Full Dictionnary of products targeted by the migration. Format: {ID: "default_code"}
TARGET_PRODUCT_IDS = {
    PRODUCT_ID_SURVIVAL: PRODUCT_DEFAULT_CODE_SURVIVAL,
    PRODUCT_ID_CHRISTMAS: PRODUCT_DEFAULT_CODE_CHRISTMAS,
    PRODUCT_ID_UNSPONSORED_CHILD: PRODUCT_DEFAULT_CODE_UNSPONSORED_CHILD,
    PRODUCT_ID_WASH: PRODUCT_DEFAULT_CODE_WASH,
    PRODUCT_ID_DISASTER: PRODUCT_DEFAULT_CODE_DISASTER,
    PRODUCT_ID_FOOD: PRODUCT_DEFAULT_CODE_FOOD,
    PRODUCT_ID_HEALTH: PRODUCT_DEFAULT_CODE_HEALTH,
}


@openupgrade.migrate()
def migrate(env, version):
    """
    Pre-migration script for 14.0.1.0.2.

    Set and modify XML_ID of some product.template:
    - Health funds product (ID 474) was without xml_id
      -> assigned 'product_template_fund_hea'
    - Food aid program product (ID 303) had an id of type '__export__.'
      -> renamed to 'product_template_fund_fda'
    - Emergency funds product (ID 238) had an id of type '__export__.'
      -> renamed to 'product_template_fund_dis'

    Remove old translations:
    - We delete entries in ir_translation for name and description.
    - Reason: Odoo protects existing translations. Deleting them forces Odoo
      to reload fresh translations from the .po files during the XML update.

    Clean One2many lines (Impact & Info):
    - We clear donation.impact.line and donation.info.line tables.
    - Reason: Moving from 'anonymous' lines (created via (0,0)) to
      'named' lines (XML records) requires a clean slate to avoid duplications.
    """
    # -------------------------------------------------------------------------
    # IDENTIFICATION & VALIDATION
    # -------------------------------------------------------------------------

    # We validate that each pair (ID, Code) exists in the database.
    # If the ID has changed or the Code has been modified, the product is ignored to
    # avoid corrupting incorrect data.
    cr = env.cr
    valid_product_ids = []

    for pid, code in TARGET_PRODUCT_IDS.items():
        cr.execute(
            """
            SELECT id FROM product_template
            WHERE id = %s AND default_code = %s
            """,
            (pid, code),
        )
        if cr.fetchone():
            valid_product_ids.append(pid)

    # If no product meets the strict criteria, we stop here.
    if not valid_product_ids:
        return

    # -------------------------------------------------------------------------
    # XML_IDS MANAGEMENT
    # -------------------------------------------------------------------------

    # Add missing XML_ID for Health product
    if PRODUCT_ID_HEALTH in valid_product_ids:
        openupgrade.add_xmlid(
            cr,
            "my_compassion_switzerland",
            "product_template_fund_hea",
            "product.template",
            PRODUCT_ID_HEALTH,
            noupdate=False,
        )

    # Rename old "__export__" IDs to proper module IDs
    xml_id_mapping = {
        PRODUCT_ID_DISASTER: "product_template_fund_dis",
        PRODUCT_ID_FOOD: "product_template_fund_fda",
    }

    for res_id, new_name in xml_id_mapping.items():
        if res_id in valid_product_ids:
            cr.execute(
                "SELECT module, name FROM ir_model_data "
                "WHERE model = %s AND res_id = %s",
                ("product.template", res_id),
            )
            res = cr.fetchone()

            if res:
                old_module, old_name = res
                openupgrade.rename_xmlids(
                    cr,
                    [
                        (
                            f"{old_module}.{old_name}",
                            f"my_compassion_switzerland.{new_name}",
                        )
                    ],
                )

    # -------------------------------------------------------------------------
    # CLEANUP OLD TRANSLATIONS
    # -------------------------------------------------------------------------

    # Force Odoo to reload translations from .po file by removing existing ones
    # for the targeted products only.
    if valid_product_ids:
        cr.execute(
            """
            DELETE FROM ir_translation
            WHERE name IN ('product.template,my_compassion_name',
                           'product.template,my_compassion_description')
            AND res_id IN %s
            """,
            (tuple(valid_product_ids),),
        )

    # -------------------------------------------------------------------------
    # CLEANUP ONE2MANY LINES
    # -------------------------------------------------------------------------

    # Cleanup Impact Lines
    # Applies to all products EXCEPT Christmas Gift (which does not use this model)
    cr.execute("SELECT to_regclass('donation_impact_line')")
    impact_table_exists = cr.fetchone()[0]

    cr.execute("SELECT to_regclass('donation_info_line')")
    info_table_exists = cr.fetchone()[0]

    if impact_table_exists:
        impact_ids_to_clean = tuple(
            pid for pid in valid_product_ids if pid != PRODUCT_ID_CHRISTMAS
        )

        if impact_ids_to_clean:
            cr.execute(
                "DELETE FROM donation_impact_line WHERE donation_id IN %s",
                (impact_ids_to_clean,),
            )

    # Cleanup Info Lines
    # Applies ONLY to Christmas Gift product
    if info_table_exists:
        if PRODUCT_ID_CHRISTMAS in valid_product_ids:
            cr.execute(
                "DELETE FROM donation_info_line WHERE donation_id = %s",
                (PRODUCT_ID_CHRISTMAS,),
            )
