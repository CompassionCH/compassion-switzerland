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
from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    singlets = env['event.registration'].search(
        [('t_shirt_type', '=', 'singlet')])
    singlets.write({'t_shirt_type': 'bikeshirt'})

    xs = env['event.registration'].search(
        [('t_shirt_size', '=', 'XS')])
    xs.write({'t_shirt_size': 'S'})
