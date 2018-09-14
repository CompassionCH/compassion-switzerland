# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Maxime Beck <mbcompte@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


def migrate(cr, version):
    if not version:
        return

    # Add "Marketing Campaign" tag to all calendar.event
    cr.execute("""
                WITH meeting_categories_to_insert as
                (
                    SELECT
                        ce.id as event_id,
                        (
                            select id from
                            calendar_event_type
                            where name = 'Marketing Campaign'
                        ) as type_id
                    FROM
                        calendar_event ce
                    WHERE campaign_event_id IS NOT NULL
                )
                INSERT INTO meeting_category_rel
                (
                    event_id,
                    type_id
                )
                SELECT
                    mcti.event_id,
                    mcti.type_id
                FROM
                    meeting_categories_to_insert mcti
                WHERE NOT EXISTS
                (
                    select 1
                    from meeting_categories_to_insert
                    where event_id = @mcti.event_id
                    and type_id = @mcti.type_id
                )
                """)
