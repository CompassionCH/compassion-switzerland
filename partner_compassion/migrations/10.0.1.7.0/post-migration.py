# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Maxime Beck
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # Insert new ambassador_details with tag "Translation" for all res_partners
    # with tag "Translator" that don't have an ambassador_detail assigned
    env.cr.execute("""
        with ambassadors_to_create as
        (
            select rp.id from res_partner rp
                inner join res_partner_res_partner_category_rel rp_cat_rel
                on rp.id = rp_cat_rel.partner_id
                inner join res_partner_category rp_cat
                on rp_cat.id = rp_cat_rel.category_id
            where rp.id not in (select partner_id from ambassador_details)
            and rp_cat.name = 'Translator'
        ),
        inserted_ambassadors as
        (
            insert into ambassador_details
            (
                partner_id,
                state
            )
            select 
                id,
                'new'
            from 
                ambassadors_to_create atc
            returning id
        )
        insert into ambassador_engagement_rel
        (
            ambassador_details_id,
            engagement_id
        )
        select 
            id,
            (select id from ambassador_engagement where name = 'Translation')
        from 
            inserted_ambassadors
    """)

    # Add tag "Translation" to ambassador_details assigned to res_partners
    # with tag "Translator"
    env.cr.execute("""
        with ambassadors_to_check as
        (
            select ad.id from ambassador_details ad
            inner join res_partner rp
            on rp.id = ad.partner_id
            inner join res_partner_res_partner_category_rel rp_cat_rel
            on rp_cat_rel.partner_id = ad.partner_id
            inner join res_partner_category rp_cat
            on rp_cat.id = rp_cat_rel.category_id
            where rp_cat.name = 'Translator'
        ),
        ambassador_engagement_rel_already_inserted as
        (
            select 
            ambassador_details_id 
            from ambassador_engagement_rel
            where ambassador_details_id in (select 
                            id 
                            from ambassadors_to_check)
            and engagement_id = (select 
                        id 
                      from ambassador_engagement 
                      where name = 'Translation')
        ),
        ambassador_engagement_rel_to_insert as
        (
            select 
            id 
            from ambassadors_to_check
            where id not in (select 
                    ambassador_details_id
                     from ambassador_engagement_rel_already_inserted)
        )
        insert into ambassador_engagement_rel
        (
            ambassador_details_id,
            engagement_id
        )
        select 
            id,
            (select id from ambassador_engagement where name = 'Translation')
        from 
            ambassador_engagement_rel_to_insert
    """)

    # Delete all tags "Translator" on res_partners
    env.cr.execute("""
        with rows_to_delete as
        (
            select 
                   category_id, 
                   partner_id
            from res_partner_res_partner_category_rel rp_cat_rel
                inner join res_partner_category rp_cat
                on rp_cat.id = rp_cat_rel.category_id
            where rp_cat.name = 'Translator'
        )
        delete from res_partner_res_partner_category_rel
        where category_id in (select category_id from rows_to_delete)
        and partner_id in (select partner_id from rows_to_delete)
    """)
