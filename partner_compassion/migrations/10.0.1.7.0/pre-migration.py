# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    if openupgrade.table_exists(env.cr, 'ambassador_details'):
        openupgrade.rename_tables(env.cr, [
            ('ambassador_details', 'advocate_details'),
            ('ambassador_engagement', 'advocate_engagement'),
            ('ambassador_engagement_rel', 'advocate_engagement_rel')
        ])
        openupgrade.rename_models(env.cr, [
            ('ambassador.details', 'advocate.details'),
            ('ambassador.engagement', 'advocate.engagement')
        ])
    if not openupgrade.column_exists(env.cr, 'res_partner',
                                     'advocate_details_id'):
        openupgrade.rename_fields(env, [
            ('res.partner', 'res_partner',
             'ambassador_details_id', 'advocate_details_id'),
        ], True)
        openupgrade.rename_columns(env.cr, {
            'advocate_engagement_rel': [
                ('ambassador_details_id', 'advocate_details_id')]
        })

    if openupgrade.column_exists(env.cr, 'res_partner',
                                 'ambassador_details_id'):
        openupgrade.drop_columns(env.cr,
                                 [('res_partner', 'ambassador_details_id')])

    # Replace field in views to avoid errors at update
    env.cr.execute("""
        UPDATE ir_ui_view
        SET arch_db = replace(arch_db, 'ambassador_details_id',
                              'advocate_details_id')
        WHERE arch_db LIKE '%ambassador_details_id%';
    """)
    # Delete old translations
    env.cr.execute("""
        DELETE FROM ir_translation
        WHERE value = 'Details of ambassador'
    """)
    # Update templates
    env.cr.execute("""
        UPDATE ir_translation
        SET value = replace(value, 'ambassador_details_id',
                            'advocate_details_id'),
            src = replace(src, 'ambassador_details_id',
                          'advocate_details_id')
        WHERE value LIKE '%ambassador_details_id%'
    """)
