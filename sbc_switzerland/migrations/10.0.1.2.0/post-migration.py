# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade
from odoo.addons.sbc_switzerland.models.translate_connector import \
    TranslateConnect


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # Define the translation source language and correct translation language
    tc = TranslateConnect()
    translated_letters = env['correspondence'].search([
        ('translator_id', '!=', False)
    ])
    for letter in translated_letters:
        if letter.direction == 'Supporter To Beneficiary':
            src_lang_id = letter.original_language_id.id
            dst_lang_id = letter.translation_language_id.id
            origin_lang_id = letter.original_language_id.id
            translate_data = tc.select_one("""
                SELECT ls.GP_libel AS src_lang, ld.GP_libel AS dst_lang
                FROM translation tr
                INNER JOIN text txt ON tr.text_id = txt.id
                INNER JOIN language ls ON txt.src_lang_id = ls.id
                INNER JOIN language ld ON txt.aim_lang_id = ld.id
                WHERE tr.letter_odoo_id = %s
            """, letter.id)
            dst_lang_iso = translate_data.get('dst_lang')
            src_lang_iso = translate_data.get('src_lang')
            if dst_lang_iso:
                dst_lang_id = env['res.lang.compassion'].search([
                    ('code_iso', '=', dst_lang_iso)]).id
            if src_lang_iso:
                origin_lang_id = env['res.lang.compassion'].search([
                    ('code_iso', '=', src_lang_iso)]).id
                src_lang_id = origin_lang_id
        else:
            translate_data = tc.select_one("""
                SELECT ls.GP_libel AS src_lang, ld.GP_libel AS dst_lang
                FROM translation tr
                INNER JOIN text txt ON tr.text_id = txt.id
                INNER JOIN language ls ON txt.src_lang_id = ls.id
                INNER JOIN language ld ON txt.aim_lang_id = ld.id
                WHERE tr.letter_odoo_id = %s
            """, letter.id)
            src_lang_id = env.ref(
                'child_compassion.lang_compassion_english').id
            dst_lang_id = letter.translation_language_id.id
            origin_lang_id = letter.original_language_id.id
            src_lang_iso = translate_data.get('src_lang')
            if src_lang_iso:
                src_lang_id = env['res.lang.compassion'].search([
                    ('code_iso', '=', src_lang_iso)]).id
            # FIX missing original language
            if not origin_lang_id:
                if letter.child_id.project_id.fcp_id.startswith('BD'):
                    origin_lang_id = env.ref(
                        'child_compassion.lang_compassion_bangali').id
                elif letter.child_id.project_id.fcp_id.startswith('ET'):
                    origin_lang_id = env.ref(
                        'child_compassion.lang_compassion_oromo').id
                else:
                    origin_lang_id = src_lang_id
        env.cr.execute("""
            UPDATE correspondence
            SET src_translation_lang_id = %s,
            translation_language_id = %s,
            original_language_id = %s
            WHERE id = %s
        """, [src_lang_id, dst_lang_id, origin_lang_id, letter.id])
