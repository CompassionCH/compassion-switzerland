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

    for registration in env['event.registration'].search([]):
        survey = registration.event_id.medical_survey_id
        medical_survey_id = env['survey.user_input'].search([
            ('partner_id', '=', registration.partner_id_id),
            ('survey_id', '=', survey.id)
        ], limit=1)
        registration.medical_survey_id = medical_survey_id
