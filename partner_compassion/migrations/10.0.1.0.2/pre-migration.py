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
from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    openupgrade.update_module_moved_fields(
        env.cr, 'res.partner', ['ambassador_quote'], 'muskathlon',
        'partner_compassion')
    env.cr.execute("""
        CREATE TABLE IF NOT EXISTS ambassador_details
    (
      id SERIAL NOT NULL
        CONSTRAINT ambassador_details_pkey
        PRIMARY KEY,
      partner_id INTEGER
        CONSTRAINT ambassador_details_partner_id_fkey
        REFERENCES res_partner
        ON DELETE SET NULL,
      thank_you_quote TEXT)
    """)

    # Move ambassador quote field into new table, ignoring empty html
    env.cr.execute("""
        INSERT INTO ambassador_details(partner_id, thank_you_quote)
SELECT id, ambassador_quote FROM res_partner
WHERE ambassador_quote not in ('',
'<p style="margin:0px 0px 9px 0px;"><br></p>',
'<p style=''margin:0px 0px 9px 0px;font-size:13px;font-family:"Lucida
 Grande", Helvetica, Verdana, Arial, sans-serif;''><br></p>',
'<p><br></p>',
 '<p style="margin: 0px 0px 9px;"><br></p>',
 '<p style=''margin:0px 0px 9px 0px;font-size:13px;font-family:"Lucida Grande"
,Helvetica,Verdana,Arial,sans-serif;''><br></p>', '<p style=''margin: 0px
 0px 9px; font-family: "Lucida Grande", Helvetica, Verdana, Arial,
 sans-serif; font-size: 13px;''><br></p>')
    """)
