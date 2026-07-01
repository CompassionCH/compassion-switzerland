import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    # Remove orphaned duplicate ir.ui.view records created during failed
    # -u all attempts. These block subsequent updates because their stale
    # arch references xpaths that no longer exist in the updated parent views.
    cr.execute(
        """
        WITH RECURSIVE orphan_views AS (
            SELECT v.id
            FROM ir_ui_view v
            WHERE NOT EXISTS (
                SELECT 1 FROM ir_model_data d
                WHERE d.model = 'ir.ui.view' AND d.res_id = v.id
            )
            AND EXISTS (
                SELECT 1 FROM ir_ui_view v2
                INNER JOIN ir_model_data d
                    ON d.model = 'ir.ui.view' AND d.res_id = v2.id
                WHERE v2.key = v.key AND v2.id != v.id
            )
            UNION ALL
            SELECT v.id
            FROM ir_ui_view v
            INNER JOIN orphan_views o ON v.inherit_id = o.id
        )
        DELETE FROM ir_ui_view WHERE id IN (SELECT id FROM orphan_views)
        """
    )
    _logger.info("Deleted %s orphaned duplicate ir.ui.view records", cr.rowcount)

    # Replace t-raw with t-out in stale view arches. t-raw was removed in
    # Odoo 18 and orphaned views may still reference it in xpath expressions.
    cr.execute(
        """
        UPDATE ir_ui_view
        SET arch_db = replace(
                replace(arch_db::text, '"t-raw"', '"t-out"'),
                't-raw=', 't-out='
            )::jsonb
        WHERE (arch_db::text LIKE '%"t-raw"%' OR arch_db::text LIKE '%t-raw=%')
          AND NOT EXISTS (
              SELECT 1 FROM ir_model_data d
              WHERE d.model = 'ir.ui.view' AND d.res_id = ir_ui_view.id
          )
        """
    )
    _logger.info("Replaced t-raw with t-out in %s orphaned views", cr.rowcount)

    # Clear stale arch_fs pointers left by openupgrade migration scripts.
    # When arch_fs points to a non-existent file, Odoo's _compute_arch skips
    # setting view.arch, leaving it False. etree.fromstring(False) then raises
    # "can only parse strings" and blocks any module upgrade.
    cr.execute(
        """
        UPDATE ir_ui_view
        SET arch_fs = NULL
        WHERE arch_fs LIKE '%openupgrade_scripts%'
        """
    )
    _logger.info("Cleared stale arch_fs pointers from %s views", cr.rowcount)
