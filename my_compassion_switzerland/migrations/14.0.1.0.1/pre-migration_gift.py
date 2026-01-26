from openupgradelib import openupgrade

# -------------------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------------------

# Specific Gift IDs (Production Database)
GIFT_ID_GENERAL = 44
GIFT_ID_FAMILY = 45
GIFT_ID_BIRTHDAY = 43

# Specific Default code
GIFT_DEFAULT_CODE_GENERAL = "gift_gen"
GIFT_DEFAULT_CODE_FAMILY = "gift_family"
GIFT_DEFAULT_CODE_BIRTHDAY = "gift_birthday"

# Full Dictionnary of gifts targeted by the migration. Format: {ID: "default_code"}
TARGET_GIFT_IDS = {
    GIFT_ID_GENERAL: GIFT_DEFAULT_CODE_GENERAL,
    GIFT_ID_FAMILY: GIFT_DEFAULT_CODE_FAMILY,
    GIFT_ID_BIRTHDAY: GIFT_DEFAULT_CODE_BIRTHDAY,
}


@openupgrade.migrate()
def migrate(env, version):
    """
    Migration script for Gifts.

    Actions:
    1. Validation: specific product IDs are checked against their default_code.
    2. Translation cleanup: remove entries in ir_translation to force Odoo
       to reload fresh translations from the .po files.
    """
    # -------------------------------------------------------------------------
    # IDENTIFICATION & VALIDATION
    # -------------------------------------------------------------------------

    # We validate that each pair (ID, Code) exists in the database.
    # If the ID has changed or the Code has been modified, the product is ignored.
    cr = env.cr
    valid_gift_ids = []

    for pid, code in TARGET_GIFT_IDS.items():
        cr.execute(
            """
            SELECT id FROM product_template
            WHERE id = %s AND default_code = %s
            """,
            (pid, code),
        )
        if cr.fetchone():
            valid_gift_ids.append(pid)

    # If no product meets the strict criteria, we stop here.
    if not valid_gift_ids:
        return

    # -------------------------------------------------------------------------
    # CLEANUP OLD TRANSLATIONS
    # -------------------------------------------------------------------------

    # Force Odoo to reload translations from .po file by removing existing ones
    # for the targeted products only.
    cr.execute(
        """
        DELETE FROM ir_translation
        WHERE name IN ('product.template,my_compassion_name',
                       'product.template,my_compassion_description')
        AND res_id IN %s
        """,
        (tuple(valid_gift_ids),),
    )
