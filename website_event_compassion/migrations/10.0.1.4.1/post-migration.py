# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
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

    # Retrieve travel info from advocates
    advocates = env['advocate.details'].search([
        ('partner_id.registration_ids', '!=', False)
    ])
    for advocate in advocates:
        registration = advocate.partner_id.registration_ids[0]
        env.cr.execute("""
            WITH adv AS (
                SELECT * FROM advocate_details
                WHERE id=%s)
            UPDATE event_registration
            SET emergency_name=adv.emergency_name,
                emergency_phone=adv.emergency_phone,
                emergency_relation_type=adv.emergency_relation_type,
                birth_name=adv.birth_name,
                passport_number=adv.passport_number,
                passport_expiration_date=adv.passport_expiration_date
            FROM adv
            WHERE event_registration.id = %s
        """, [advocate.id, registration.id])
