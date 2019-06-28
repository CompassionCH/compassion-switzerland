# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Théo Nikles <theo.nikles@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # Reload Muskathlon medical survey data
    openupgrade.load_data(
        cr=env.cr,
        module_name='muskathlon',
        filename='data/survey_muskathlon_medical_infos.xml',
    )
