# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


def migrate(cr, version):
    if not version:
        return

    cr.execute("""
    update ir_translation
    set value = replace(value, 'icp', 'fcp')
    where value like '%icp%';
    update ir_translation
    set value = replace(value, 'ICP', 'FCP')
    where value like '%ICP%';
    update ir_translation
    set src = replace(src, 'icp', 'fcp')
    where src like '%icp%';
    update ir_translation
    set src = replace(src, 'ICP', 'FCP')
    where src like '%ICP%';
    """)
