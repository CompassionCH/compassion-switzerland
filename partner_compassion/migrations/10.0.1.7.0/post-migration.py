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


def migrate(cr, version):
    if not version:
        return

    # Insert new advocate_details with tag "Translation" for all res_partners
    # with tag "Translator" that don't have an advocate_detail assigned
    cr.execute("""
        with advocates_to_create as
        (
            select rp.id from res_partner rp
                inner join res_partner_res_partner_category_rel rp_cat_rel
                on rp.id = rp_cat_rel.partner_id
                inner join res_partner_category rp_cat
                on rp_cat.id = rp_cat_rel.category_id
            where rp.id not in (select partner_id from advocate_details)
            and rp_cat.name = 'Translator'
        ),
        inserted_advocates as
        (
            insert into advocate_details
            (
                partner_id,
                state
            )
            select
                id,
                'new'
            from
                advocates_to_create atc
            returning id
        )
        insert into advocate_engagement_rel
        (
            advocate_details_id,
            engagement_id
        )
        select
            id,
            (select id from advocate_engagement where name = 'Translation')
        from
            inserted_advocates
    """)

    # Add tag "Translation" to advocate_details assigned to res_partners
    # with tag "Translator"
    cr.execute("""
        with advocates_to_check as
        (
            select ad.id from advocate_details ad
            inner join res_partner rp
            on rp.id = ad.partner_id
            inner join res_partner_res_partner_category_rel rp_cat_rel
            on rp_cat_rel.partner_id = ad.partner_id
            inner join res_partner_category rp_cat
            on rp_cat.id = rp_cat_rel.category_id
            where rp_cat.name = 'Translator'
        ),
        advocate_engagement_rel_already_inserted as
        (
            select
            advocate_details_id
            from advocate_engagement_rel
            where advocate_details_id in (select
                            id
                            from advocates_to_check)
            and engagement_id = (select
                        id
                      from advocate_engagement
                      where name = 'Translation')
        ),
        advocate_engagement_rel_to_insert as
        (
            select
            id
            from advocates_to_check
            where id not in (select
                    advocate_details_id
                     from advocate_engagement_rel_already_inserted)
        )
        insert into advocate_engagement_rel
        (
            advocate_details_id,
            engagement_id
        )
        select
            id,
            (select id from advocate_engagement where name = 'Translation')
        from
            advocate_engagement_rel_to_insert
    """)

    # Delete all tags "Translator" on res_partners
    cr.execute("""
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

    # Update missing links of partner to advocate
    cr.execute("""
        UPDATE res_partner p
        SET advocate_details_id = (SELECT a.id from advocate_details a
                                   WHERE a.partner_id = p.id)
    """)

    # Set new translators active if they already translated
    cr.execute("""
        UPDATE advocate_details
        SET state = 'active'
        FROM correspondence
        WHERE advocate_details.partner_id = correspondence.translator_id;
    """)
