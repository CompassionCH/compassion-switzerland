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

    # Correct commitment numbers
    env.cr.execute("""
select partner_id, commitment_number, count(*)
from recurring_contract
where state not in ('terminated','cancelled')
and partner_id is not null
and child_id is not null
group by partner_id, commitment_number
having count(*) > 1
    """)
    correct_number(env, env.cr.fetchall())
    env.cr.execute("""
select correspondent_id, commitment_number, count(*)
from recurring_contract
where state not in ('terminated','cancelled')
and partner_id is not null
and child_id is not null
group by correspondent_id, commitment_number
having count(*) > 1
        """)
    correct_number(env, env.cr.fetchall())


def correct_number(env, query_results):
    cancel_config = env.ref(
        'partner_communication_switzerland.sponsorship_cancellation')
    comm_obj = env['partner.communication.job'].with_context(
        skip_pdf_count=True)
    for row in query_results:
        partner_id = row[0]
        commitment_number = row[1]
        all_sponsorships_from_sponsor = env['recurring.contract'].search([
            '|', ('partner_id', '=', partner_id),
            ('correspondent_id', '=', partner_id),
            ('state', 'not in', ['terminated', 'cancelled']),
            ('child_id', '!=', False)
        ])
        problem_sponsorships = all_sponsorships_from_sponsor.filtered(
            lambda s: s.commitment_number == commitment_number)
        new_number = max(all_sponsorships_from_sponsor.mapped(
            'commitment_number')) + 1
        for sponsorship in problem_sponsorships:
            sponsorship.commitment_number = new_number
            new_number += 1

        # Create communication to remember to send new BVR to the people.
        # Use cancellation config to avoid generating any attached PDF
        comm_obj.create({
            'partner_id': partner_id,
            'object_ids': problem_sponsorships.ids,
            'config_id': cancel_config.id,
            'body_html':
            "Please change the config to Yearly Payment Slips and use this "
            "communication to send new Gift BVR to the sponsor, as his "
            "BVR reference for gifts was corrected."
        })
