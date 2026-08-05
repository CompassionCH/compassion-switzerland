from openupgradelib import openupgrade


def migrate(cr, version):
    """T1523: the German and Italian translations of the onboarding
    photo-by-post report template had mistranslated CSS property names
    (e.g. "width" -> "Breite"/"larghezza"), making the #map positioning rule
    invalid CSS and hiding the country map on German/Italian cards. Overwrite
    those two translations with the known-good French one.
    """
    openupgrade.logged_query(
        cr,
        """
UPDATE ir_ui_view
SET arch_db = jsonb_set(
    jsonb_set(arch_db, '{de_DE}', arch_db->'fr_CH'),
    '{it_IT}', arch_db->'fr_CH'
)
WHERE id = (
    SELECT res_id FROM ir_model_data
    WHERE module = 'partner_communication_switzerland'
      AND name = 'onboarding_photo_by_post'
      AND model = 'ir.ui.view'
)
AND arch_db ? 'fr_CH';
        """,
    )
