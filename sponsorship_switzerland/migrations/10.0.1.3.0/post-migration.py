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

# When a child correspondent is also the partner of another child,
# the commitment number of the recurring contract is potentially
# the same for both sponsorship.
#
# This generates the same reference number on the BVR and results in
# confusion.


def migrate(cr, version):
    if not version:
        return

    # Update problematic records with a new commitment number
    # that starts at 123 and is incremented for every updated
    # record.
    cr.execute("""
    with records_to_update as
    (
        select
            rcp.id,
            rcp.partner_id as correspondent_id,
            rcc.partner_id,
            rcp.commitment_number as correspondent_cn,
            rcc.commitment_number as partner_cn
        from recurring_contract rcp
        left join recurring_contract rcc
        on rcp.partner_id = rcc.correspondent_id
        where rcp.partner_id != rcc.partner_id and
        rcp.commitment_number = rcc.commitment_number
    )
    update recurring_contract
    set commitment_number=records_to_update.new_commitment_number
    from
        (select
            id,
            (row_number() over (order by id) + 123)
                as new_commitment_number
         from records_to_update) as records_to_update
    where recurring_contract.id = records_to_update.id
    """)
