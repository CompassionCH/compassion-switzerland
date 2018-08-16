# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nicolas Bornand
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    category_env = env['res.partner.category']
    ambassador_env = env['ambassador.details']
    partner_env = env['res.partner']

    sport_tags = category_env.search([
        '|',
        ('name', 'ilike', 'muskathlon'),
        ('name', 'in', ['stralugano', 'run4charity', 'HalfMarathonStraLugano',
                        'sportsperson', '10kmStraLugano', 'KidsrunStralugano'])
    ])
    translator_tag = category_env.search([('name', 'ilike', 'Translator')])
    church_tag = category_env.search([('name', 'ilike', 'Church Advocate')])

    tag_mappings = [
        (sport_tags, env.ref('partner_compassion.engagement_sport')),
        (translator_tag, env.ref('partner_compassion.engagement_translation')),
        (church_tag, env.ref('partner_compassion.engagement_church'))
    ]
    ambassador_tags = category_env.search([('name', 'ilike', 'Advocate')])
    all_tags = sport_tags + translator_tag + church_tag + ambassador_tags

    already_ambassador = ambassador_env.search([]).mapped('partner_id')
    partner_eligible_as_ambassador = partner_env.search([
        ('category_id', 'in', all_tags.ids)
    ])
    for partner in partner_eligible_as_ambassador - already_ambassador:
        new_ambassador = env['ambassador.details'].create({
            'partner_id': partner.id,
            'quote': 'Automatically migrated'
        })
        for partner_tags, ambassador_engagement in tag_mappings:
            if len(partner.category_id & partner_tags) > 0:
                new_ambassador.engagement_ids += ambassador_engagement

    (church_tag + ambassador_tags).unlink()
