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

    # Update Muskathlon events
    events = env['crm.event.compassion'].search([
        ('odoo_event_id', '!=', False)])
    events.write({'website_muskathlon': True})
    events.mapped('odoo_event_id').write({
        'fundraising': True,
        'donation_product_id': env.ref('sponsorship_switzerland.'
                                       'product_template_fund_4mu').id
    })
