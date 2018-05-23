# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import re

from openupgradelib import openupgrade
from pyquery import PyQuery


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # Move field ambassador quote from module Muskathlon
    openupgrade.update_module_moved_fields(
        env.cr, 'res.partner', ['ambassador_quote'], 'muskathlon',
        'partner_compassion')

    # Add field to track ambassadors migrated
    env.cr.execute("""
        ALTER TABLE res_partner ADD COLUMN quote_migrated boolean;
    """)

    # Move ambassador quote field into new table, ignoring empty html
    _split_ambassador_quote(env)


def _split_ambassador_quote(env):
    """ Parse ambassador quote to split image and text into fields. """
    env.cr.execute("""
        SELECT id, ambassador_quote FROM res_partner
        WHERE ambassador_quote LIKE '%tbody%'
    """)
    data = env.cr.fetchall()
    remove_html_pattern = re.compile(r'<.*?>')
    update_sql = """
        UPDATE res_partner
        SET ambassador_quote = %s, quote_migrated=true
        WHERE id = %s
    """
    partner_obj = env['res.partner'].with_context(tracking_disable=True)
    for aid, quote in data:
        html = PyQuery(quote)
        image_src = html("img").attr("src")
        if image_src:
            image_raw = image_src.split("base64,")
            image_data = False
            if len(image_raw) > 1:
                image_data = image_raw[1]
            elif 'web' in image_src:
                img_id = int(image_src.split('/')[-1])
                image_data = env['ir.http'].binary_content(
                    id=img_id, env=env)[2]
            if image_data:
                partner_obj.browse(aid).image = image_data

        thankyou_text = remove_html_pattern.sub("", quote).strip()
        env.cr.execute(update_sql, [thankyou_text, aid])
