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
from odoo import fields
from odoo.tests.common import HttpCase


class TestWebsiteEvent(HttpCase):

    def test_website_event_registration(self):
        event = self.env['crm.event.compassion'].create({
            'name': 'Test website event',
            'type': 'tour',
            'start_date': fields.Datetime.now(),
            'end_date': fields.Datetime.now(),
            'hold_start_date': fields.Datetime.now(),
            'number_allocate_children': 0,
            'planned_sponsorships': 0,
        })

        # Test registration is correctly set
        price = 200
        registration_wizard = self.env['crm.event.compassion.open.wizard']\
            .with_context(active_id=event.id).create({
                'registration_fee': price,
                'product_id': 1,
                'seats_min': 10,
                'seats_max': 30,
            })
        registration_wizard.open_event()
        odoo_event = event.odoo_event_id
        self.assertEqual(odoo_event.event_ticket_ids[:1].price, price)
