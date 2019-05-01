# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


def migrate(cr, version):
    if not version:
        return

    # Remove data to avoid record deletion
    cr.execute("""
        SELECT value FROM ir_config_parameter WHERE key='email.banner.url.open'
    """)
    link = cr.dictfetchone()['value']
    cr.execute("""
            INSERT INTO ir_config_parameter (key, value) VALUES
                ('email.banner.url.open.fr_CH', %s),
                ('email.banner.url.open.it_IT', %s),
                ('email.banner.url.open.de_DE', %s);
    """, [link]*3)
    cr.execute("""
        DELETE FROM ir_config_parameter WHERE key='email.banner.url.open'
    """)
