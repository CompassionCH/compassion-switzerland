# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # Delete old Muskathlon medical surveys
    muskathlon_survey = env['survey.survey'].search([
        ('title', '=', 'Muskathlon medical survey')])
    survey_inputs = env['survey.user_input'].search([
        ('survey_id', '=', muskathlon_survey.id)
    ])
    survey_inputs.unlink()
    muskathlon_survey.unlink()

    # Delete old xml data
    env.cr.execute("""
        DELETE FROM ir_model_data
        WHERE name LIKE 'muskathlon_1%' OR name = 'muskathlon_form';
    """)
