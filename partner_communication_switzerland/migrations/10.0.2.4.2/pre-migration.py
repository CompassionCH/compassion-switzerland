# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Samuel Fringeli <samuel.fringeli@me.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # Change new dossier communications
    old_dossiers = env.ref(
        'partner_communication_switzerland.planned_dossier_correspondent'
    ) + env.ref('partner_communication_switzerland.planned_dossier_payer')
    new_dossier = env.ref('partner_communication_switzerland.planned_dossier')
    env.cr.execute("""
        UPDATE partner_communication_job
        SET config_id = %s
        WHERE config_id = ANY (%s)
    """, [new_dossier.id, old_dossiers.ids])
