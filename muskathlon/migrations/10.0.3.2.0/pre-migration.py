# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


def migrate(cr, version):
    if not version:
        return

    cr.execute("""
        UPDATE event_registration
        SET t_shirt_size = 'S' where t_shirt_size = 'XS';
        UPDATE event_registration
        SET t_shirt_type = 'bikeshirt' where t_shirt_type = 'singlet';
    """)
